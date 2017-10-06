# Copyright (C) 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Forked and modified from warchildmd's repo "https://github.com/warchildmd/google-assistant-hotword-raspi"

"""Sample that implements gRPC client for Google Assistant API."""

import json
import logging
import os.path
import subprocess
import os
import click
import grpc
import google.auth.transport.grpc
import google.auth.transport.requests
import google.oauth2.credentials
import RPi.GPIO as GPIO
from google.assistant.embedded.v1alpha1 import embedded_assistant_pb2
from google.rpc import code_pb2
from tenacity import retry, stop_after_attempt, retry_if_exception
from local-actions import Action

try:
    from googlesamples.assistant.grpc import (
        assistant_helpers,
        audio_helpers
    )
except SystemError:
    import assistant_helpers
    import audio_helpers


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

#Indicator pins declaration
GPIO.setup(05,GPIO.OUT)
GPIO.setup(06,GPIO.OUT)
GPIO.output(05, GPIO.LOW)
GPIO.output(06, GPIO.LOW)

gassistaction = Action()

ASSISTANT_API_ENDPOINT = 'embeddedassistant.googleapis.com'
END_OF_UTTERANCE = embedded_assistant_pb2.ConverseResponse.END_OF_UTTERANCE
DIALOG_FOLLOW_ON = embedded_assistant_pb2.ConverseResult.DIALOG_FOLLOW_ON
CLOSE_MICROPHONE = embedded_assistant_pb2.ConverseResult.CLOSE_MICROPHONE
DEFAULT_GRPC_DEADLINE = 60 * 3 + 5



class Assistant():
    def __init__(self):
        self.api_endpoint = ASSISTANT_API_ENDPOINT
        self.credentials = os.path.join(click.get_app_dir('google-oauthlib-tool'),
                                   'credentials.json')
        # Setup logging.
        logging.basicConfig() # filename='assistant.log', level=logging.DEBUG if self.verbose else logging.INFO)
        self.logger = logging.getLogger("assistant")
        self.logger.setLevel(logging.DEBUG)

        # Load OAuth 2.0 credentials.
        try:
            with open(self.credentials, 'r') as f:
                self.credentials = google.oauth2.credentials.Credentials(token=None,
                                                                    **json.load(f))
                self.http_request = google.auth.transport.requests.Request()
                self.credentials.refresh(self.http_request)
        except Exception as e:
            logging.error('Error loading credentials: %s', e)
            logging.error('Run google-oauthlib-tool to initialize '
                          'new OAuth 2.0 credentials.')
            return

        # Create an authorized gRPC channel.
        self.grpc_channel = google.auth.transport.grpc.secure_authorized_channel(
            self.credentials, self.http_request, self.api_endpoint)
        logging.info('Connecting to %s', self.api_endpoint)

        self.audio_sample_rate = audio_helpers.DEFAULT_AUDIO_SAMPLE_RATE
        self.audio_sample_width = audio_helpers.DEFAULT_AUDIO_SAMPLE_WIDTH
        self.audio_iter_size = audio_helpers.DEFAULT_AUDIO_ITER_SIZE
        self.audio_block_size = audio_helpers.DEFAULT_AUDIO_DEVICE_BLOCK_SIZE
        self.audio_flush_size = audio_helpers.DEFAULT_AUDIO_DEVICE_FLUSH_SIZE
        self.grpc_deadline = DEFAULT_GRPC_DEADLINE

        # Create Google Assistant API gRPC client.
        self.assistant = embedded_assistant_pb2.EmbeddedAssistantStub(self.grpc_channel)

        # Stores an opaque blob provided in ConverseResponse that,
        # when provided in a follow-up ConverseRequest,
        # gives the Assistant a context marker within the current state
        # of the multi-Converse()-RPC "conversation".
        # This value, along with MicrophoneMode, supports a more natural
        # "conversation" with the Assistant.
        self.conversation_state_bytes = None

        # Stores the current volument percentage.
        # Note: No volume change is currently implemented in this sample
        self.volume_percentage = 80

    def assist(self):
        # Configure audio source and sink.
        self.audio_device = None
        self.audio_source = self.audio_device = (
            self.audio_device or audio_helpers.SoundDeviceStream(
                sample_rate=self.audio_sample_rate,
                sample_width=self.audio_sample_width,
                block_size=self.audio_block_size,
                flush_size=self.audio_flush_size
            )
        )

        self.audio_sink = self.audio_device = (
            self.audio_device or audio_helpers.SoundDeviceStream(
                sample_rate=self.audio_sample_rate,
                sample_width=self.audio_sample_width,
                block_size=self.audio_block_size,
                flush_size=self.audio_flush_size
            )
        )

        # Create conversation stream with the given audio source and sink.
        self.conversation_stream = audio_helpers.ConversationStream(
            source=self.audio_source,
            sink=self.audio_sink,
            iter_size=self.audio_iter_size,
            sample_width=self.audio_sample_width
        )
        restart = False
        continue_conversation = True
        try:
            while continue_conversation:
                continue_conversation = False
                subprocess.Popen(["aplay", "/home/pi/GassistPi/sample-audio-files/Fb.wav"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.conversation_stream.start_recording()
		GPIO.output(05,GPIO.HIGH)
                self.logger.info('Recording audio request.')

                def iter_converse_requests():
                    for c in self.gen_converse_requests():
                        assistant_helpers.log_converse_request_without_audio(c)
                        yield c
                    self.conversation_stream.start_playback()

                # This generator yields ConverseResponse proto messages
                # received from the gRPC Google Assistant API.
                for resp in self.assistant.Converse(iter_converse_requests(),
                                                    self.grpc_deadline):
                    assistant_helpers.log_converse_response_without_audio(resp)
                    if resp.error.code != code_pb2.OK:
                        self.logger.error('server error: %s', resp.error.message)
                        break
                    if resp.event_type == END_OF_UTTERANCE:
                        self.logger.info('End of audio request detected')
			GPIO.output(05,GPIO.LOW)
                        self.conversation_stream.stop_recording()
                    if resp.result.spoken_request_text:
                        usrcmd=str(resp.result.spoken_request_text).lower
                        if 'trigger' in usrcmd:
                            gassistaction(usrcmd)
                            return continue_conversation

                        else:
                            continue
                        self.logger.info('Transcript of user request: "%s".',
                                     resp.result.spoken_request_text)
			GPIO.output(05,GPIO.LOW)
       			GPIO.output(06,GPIO.HIGH)
                        self.logger.info('Playing assistant response.')
                    if len(resp.audio_out.audio_data) > 0:
                        self.conversation_stream.write(resp.audio_out.audio_data)
                    if resp.result.spoken_response_text:
                        self.logger.info(
                            'Transcript of TTS response '
                            '(only populated from IFTTT): "%s".',
                            resp.result.spoken_response_text)
                    if resp.result.conversation_state:
                        self.conversation_state_bytes = resp.result.conversation_state
                    if resp.result.volume_percentage != 0:
                        volume_percentage = resp.result.volume_percentage
                        self.logger.info('Volume should be set to %s%%', volume_percentage)
                    if resp.result.microphone_mode == DIALOG_FOLLOW_ON:
                        continue_conversation = True
			GPIO.output(06,GPIO.LOW)
       			GPIO.output(05,GPIO.HIGH)
                        self.logger.info('Expecting follow-on query from user.')
                self.logger.info('Finished playing assistant response.')
		GPIO.output(06,GPIO.LOW)
       		GPIO.output(05,GPIO.LOW)
                self.conversation_stream.stop_playback()
        except Exception as e:
            self._create_assistant()
            self.logger.exception('Skipping because of connection reset')
            restart = True
        try:
            self.conversation_stream.close()
            if restart:
                self.assist()
        except Exception:
            self.logger.error('Failed to close conversation_stream.')

    def _create_assistant(self):
        # Create gRPC channel
        grpc_channel = google.auth.transport.grpc.secure_authorized_channel(
            self.credentials, self.http_request, self.api_endpoint)

        self.logger.info('Connecting to %s', self.api_endpoint)
        # Create Google Assistant API gRPC client.
        self.assistant = embedded_assistant_pb2.EmbeddedAssistantStub(grpc_channel)

    def is_grpc_error_unavailable(e):
        is_grpc_error = isinstance(e, grpc.RpcError)
        if is_grpc_error and (e.code() == grpc.StatusCode.UNAVAILABLE):
            logging.error('grpc unavailable error: %s', e)
            return True
        return False

    @retry(reraise=True, stop=stop_after_attempt(3),
           retry=retry_if_exception(is_grpc_error_unavailable))

    # This generator yields ConverseRequest to send to the gRPC
    # Google Assistant API.
    def gen_converse_requests(self):
        """Yields: ConverseRequest messages to send to the API."""
        converse_state = None
        if self.conversation_state_bytes:
            logging.debug('Sending converse_state: %s',
                          self.conversation_state_bytes)
            converse_state = embedded_assistant_pb2.ConverseState(
                conversation_state=self.conversation_state_bytes,
            )
        config = embedded_assistant_pb2.ConverseConfig(
            audio_in_config=embedded_assistant_pb2.AudioInConfig(
                encoding='LINEAR16',
                sample_rate_hertz=self.conversation_stream.sample_rate,
            ),
            audio_out_config=embedded_assistant_pb2.AudioOutConfig(
                encoding='LINEAR16',
                sample_rate_hertz=self.conversation_stream.sample_rate,
                volume_percentage=self.conversation_stream.volume_percentage,
            ),
            converse_state=converse_state
        )
        # The first ConverseRequest must contain the ConverseConfig
        # and no audio data.
        yield embedded_assistant_pb2.ConverseRequest(config=config)
        for data in self.conversation_stream:
            # Subsequent requests need audio data, but not config.
            yield embedded_assistant_pb2.ConverseRequest(audio_in=data)
