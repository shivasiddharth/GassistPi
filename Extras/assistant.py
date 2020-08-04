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

from ctypes import (CFUNCTYPE, POINTER,
                    cast, cdll, util,
                    c_bool, c_char, c_char_p, c_int, c_uint, c_void_p)

import json
import os

from .auth_helpers import CredentialsRefresher
from .event import Event, IterableEventQueue
from .version import __version__

EVENT_CALLBACK = CFUNCTYPE(None, c_int, POINTER(c_char))

LIBRARY_NAME = 'libassistant_embedder.so'


class Assistant(object):
    """Client for the Google Assistant Library.

    Provides basic control functionality and lifecycle handling for
    the Google Assistant. It is best practice to use the Assistant as
    a ``ContextManager``::

        with Assistant(credentials, device_model_id) as assistant:

    This allows the underlying native implementation to properly
    handle memory management.

    Once :meth:`~google.assistant.library.Assistant.start` is called,
    the Assistant generates a stream of Events relaying the various
    states the Assistant is currently in, for example::

        ON_CONVERSATION_TURN_STARTED
        ON_END_OF_UTTERANCE
        ON_RECOGNIZING_SPEECH_FINISHED:
            {'text': 'what time is it'}
        ON_RESPONDING_STARTED:
            {'is_error_response': False}
        ON_RESPONDING_FINISHED
        ON_CONVERSATION_TURN_FINISHED:
            {'with_follow_on_turn': False}

    See :class:`~google.assistant.library.event.EventType` for details
    on all events and their arguments.

    Glossary:

    - *Hotword*: The phrase the Assistant listens for when not muted::

        "OK Google" OR "Hey Google"

    - *Turn*: A single user request followed by a response from the Assistant.

    - *Conversation*: One or more turns which result in a desired final result
      from the Assistant::

        "What time is it?" -> "The time is 6:24 PM" OR
        "Set a timer" -> "Okay, for how long?" ->
        "5 minutes" -> "Sure, 5 minutes, starting now!"

    Args:
        credentials (google.oauth2.credentials.Credentials): The user's
            Google OAuth2 credentials.
        device_model_id (str): The device_model_id that was registered for
            your project with Google. This must not be an empty string.

    Raises:
        ValueError: If ``device_model_id`` was left as None or empty.
    """

    def __init__(self, credentials, device_model_id):
        if not device_model_id:
            raise ValueError("device_model_id must be a non-empty string")

        self._event_queue = IterableEventQueue()
        self._load_lib()
        self._credentials_refresher = None
        self._shutdown = False

        self._event_callback = EVENT_CALLBACK(self)
        self._inst = c_void_p(
            self._lib.assistant_new(
                self._event_callback,
                device_model_id.encode('ASCII'),None))

        self._credentials_refresher = CredentialsRefresher(
            credentials, self._set_credentials)
        self._credentials_refresher.start()

    def __enter__(self):
        """Returns self."""
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """Frees allocated memory belonging to the Assistant."""
        if self._credentials_refresher:
            self._credentials_refresher.stop()
            self._credentials_refresher = None
        self._shutdown = True
        self._lib.assistant_free(self._inst)

    def __call__(self, event_type, event_data):
        """Adds a new event to the event queue returned from
        :meth:`~google.assistant.library.Assistant.start`().

        The native Assistant will generate events such as:

            event_type: 5
            event_data: "{ 'text': 'what time is it' }"

        which are then converted to a more Pythonic representation here
        and then offered to the queue.

        Args:
            event_type (int): A numeric id corresponding to an event in
                google.assistant.event.EventType.
            event_data (ctypes.POINTER(ctypes.c_char)): A serialized JSON
                string with key/value pairs for event arguments.
        """
        # Ignore any events we receive from ctypes once we have freed
        # the underlying native library.
        if self._shutdown:
            return

        args = None
        if event_data:
            # Get the string pointed to by the pointer.
            event_bytes = cast(event_data, c_char_p).value
            args = json.loads(event_bytes.decode('UTF-8'))
            # Free the string once we have used it.
            self._libc.free(event_data)

        event = Event.New(event_type, args, device_id=self.device_id)
        self._event_queue.offer(event)

    def start(self):
        """Starts the Assistant, which includes listening for a hotword.

        Once :meth:`~google.assistant.library.Assistant.start` is
        called, the Assistant will begin processing data from the
        'default' ALSA audio source, listening for the hotword. This
        will also start other services provided by the Assistant, such
        as timers/alarms. This method can only be called once. Once
        called, the Assistant will continue to run until ``__exit__``
        is called.

        Returns:
            google.assistant.event.IterableEventQueue:
                A queue of events that notify of changes to the Assistant
                state.
        """
        self._lib.assistant_start(self._inst)
        return self._event_queue

    def set_mic_mute(self, is_muted):
        """Stops the Assistant from listening for the hotword.

        Allows for disabling the Assistant from listening for the hotword.
        This provides functionality similar to the privacy button on the back
        of Google Home.

        This method is a no-op if the Assistant has not yet been started.

        Args:
            is_muted (bool):
                True stops the Assistant from listening and False
                allows it to start again.
        """
        self._lib.assistant_set_mic_mute(self._inst, is_muted)

    def start_conversation(self):
        """Manually starts a new conversation with the Assistant.

        Starts both recording the user's speech and sending it to Google,
        similar to what happens when the Assistant hears the hotword. If the
        Assistant has not been started or the microphone is muted then this
        method is a no-op.
        """
        self._lib.assistant_start_conversation(self._inst)

    def stop_conversation(self):
        """Stops any active conversation with the Assistant.

        The Assistant could be listening to the user's query OR responding. If
        there is no active conversation or the Assistant has not been started
        then this method is a no-op.
        """
        self._lib.assistant_stop_conversation(self._inst)

    def send_text_query(self, query):
        """Sends |query| to the Assistant as if it were spoken by the user.

        This will behave the same as a user speaking the hotword and making
        a query OR speaking the answer to a follow-on query. If the Assistant
        has not been started then this method is a no-op.

        Args:
            query (str):
                The text query to send to the Assistant.
        """
        self._lib.assistant_send_text_query(self._inst, query.encode('ASCII'))

    @property
    def device_id(self):
        """Returns the device ID generated by the Assistant.

        This value identifies your device to the server when using services
        such as Google Device Actions. This property is only filled AFTER
        :meth:`~google.assistant.library.Assistant.start` has been called.

        Returns:
            str:
                The device id once
                :meth:`~google.assistant.library.Assistant.start` has
                been called, empty string otherwise.
        """
        return self._lib.assistant_device_id(self._inst).decode('UTF-8')

    @staticmethod
    def __version__():
        """Returns the version of the Assistant.

        Returns:
            dict: Contains the version of the Assistant being used.
        """
        return __version__

    @staticmethod
    def __version_str__():
        """Returns the version of the Assistant as a string.

        Returns:
            dict: Contains the version of the Assistant being used.
        """
        return '%s core: %d' % (__version__['package'], __version__['core'])

    def _set_credentials(self, credentials):
        """Sets Google account OAuth2 credentials for the current user.

        Args:
            credentials (google.oauth2.credentials.Credentials): OAuth2
                Google account credentials for the current user.
        """
        # The access_token should always be made up of only ASCII
        # characters so this encoding should never fail.
        access_token = credentials.token.encode('ASCII')
        self._lib.assistant_set_access_token(self._inst,
                                             access_token, len(access_token))

    def _load_lib(self):
        """Dynamically loads the Google Assistant Library.

        Automatically selects the correct shared library for the current
        platform and sets up bindings to its C interface.
        """
        lib_path = os.path.join(os.path.dirname(__file__), LIBRARY_NAME)
        self._lib = cdll.LoadLibrary(lib_path)

        # void* assistant_new(EventCallback listener, const char*
        # device_model_id);
        self._lib.assistant_new.argtypes = [EVENT_CALLBACK, c_char_p, c_char_p]
        self._lib.assistant_new.restype = c_void_p

        # void assistant_free(void* instance);
        self._lib.assistant_free.argtypes = [c_void_p]
        self._lib.assistant_free.restype = None

        # void assistant_start(void* assistant);
        self._lib.assistant_start.argtypes = [c_void_p]
        self._lib.assistant_start.restype = None

        # const char* assistant_device_id(void* assistant);
        self._lib.assistant_device_id.argtypes = [c_void_p]
        self._lib.assistant_device_id.restype = c_char_p

        # void assistant_set_access_token(
        #     void* assistant, const char* access_token, size_t length);
        self._lib.assistant_set_access_token.argtypes = [
            c_void_p, c_char_p, c_uint
        ]
        self._lib.assistant_set_access_token.restype = None

        # void assistant_set_mic_mute(void* assistant, bool is_muted);
        self._lib.assistant_set_mic_mute.argtypes = [c_void_p, c_bool]
        self._lib.assistant_set_mic_mute.restype = None

        # void assistant_start_conversation(void* assistant);
        self._lib.assistant_start_conversation.argtypes = [c_void_p]
        self._lib.assistant_start_conversation.restype = None

        # void assistant_stop_conversation(void* assistant);
        self._lib.assistant_stop_conversation.argtypes = [c_void_p]
        self._lib.assistant_stop_conversation.restype = None

        # void assistant_send_text_query(void* assistant, const char* query);
        self._lib.assistant_send_text_query.argtypes = [c_void_p, c_char_p]
        self._lib.assistant_send_text_query.restype = None

        # const char* assistant_version();
        self._lib.assistant_version.argtypes = None
        self._lib.assistant_version.restype = c_char_p

        self._libc = cdll.LoadLibrary(util.find_library('c'))
        self._libc.free.argtypes = [c_void_p]
        self._libc.free.restype = None
