# coding: utf-8
#
# Copyright (C) 2020, Team Kodi
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Functions to interact with various web site APIs."""

from __future__ import absolute_import, unicode_literals

import json
import time
import socket

try:
    import xbmc
except ModuleNotFoundError:
    # only used for logging HTTP calls, not available nor needed for testing
    xbmc = None

# from pprint import pformat
try: #PY2 / PY3
    from urllib2 import Request, urlopen
    from urllib2 import URLError
    from urllib import urlencode
except ImportError:
    from urllib.request import Request, urlopen
    from urllib.error import URLError
    from urllib.parse import urlencode
try:
    from typing import Text, Optional, Union, List, Dict, Any  # pylint: disable=unused-import
    InfoType = Dict[Text, Any]  # pylint: disable=invalid-name
except ImportError:
    pass

HEADERS = {}


def set_headers(headers):
    HEADERS.clear()
    HEADERS.update(headers)


def load_info(url, params=None, default=None, resp_type = 'json', max_retries=3, retry_delay=1):
    # type: (Text, Optional[Dict[Text, Union[Text, List[Text]]]]) -> Union[dict, list]
    """
    Load info from external api with retry logic for network issues

    :param url: API endpoint URL
    :param params: URL query params
    :param default: object to return if there is an error
    :param resp_type: what to return to the calling function
    :param max_retries: maximum number of retry attempts
    :param retry_delay: delay between retries in seconds
    :return: API response or default on error
    """
    if params:
        url = url + '?' + urlencode(params)
    if xbmc:
        xbmc.log('Calling URL "{}"'.format(url), xbmc.LOGDEBUG)
    if HEADERS:
        xbmc.log(str(HEADERS), xbmc.LOGDEBUG)
    
    for attempt in range(max_retries + 1):
        req = Request(url, headers=HEADERS)
        try:
            response = urlopen(req, timeout=30)  # Add timeout
            if resp_type.lower() == 'json':
                resp = json.loads(response.read().decode('utf-8'))
            else:
                resp = response.read().decode('utf-8')
            # xbmc.log('the api response:\n{}'.format(pformat(resp)), xbmc.LOGDEBUG)
            return resp
            
        except URLError as e:
            error_msg = ''
            is_retryable = False
            
            if hasattr(e, 'reason'):
                error_msg = 'failed to reach the remote site\nReason: {}'.format(e.reason)
                # Check if it's a connection reset (errno 104) or similar network issue
                if isinstance(e.reason, socket.error):
                    errno_val = getattr(e.reason, 'errno', None)
                    if errno_val in [104, 110, 111, 113]:  # Connection reset, timeout, refused, no route
                        is_retryable = True
            elif hasattr(e, 'code'):
                error_msg = 'remote site unable to fulfill the request\nError code: {}'.format(e.code)
                # Retry on server errors (5xx), but not client errors (4xx)
                if 500 <= e.code < 600:
                    is_retryable = True
            
            if attempt < max_retries and is_retryable:
                if xbmc:
                    xbmc.log('Network error on attempt {}/{}: {}. Retrying in {} seconds...'.format(
                        attempt + 1, max_retries + 1, error_msg, retry_delay), xbmc.LOGWARNING)
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                continue
            else:
                # Final attempt failed or non-retryable error
                theerror = {'error': error_msg}
                if xbmc:
                    xbmc.log('Final network error: {}'.format(error_msg), xbmc.LOGERROR)
                if default is not None:
                    return default
                else:
                    return theerror
        
        except socket.timeout:
            if attempt < max_retries:
                if xbmc:
                    xbmc.log('Request timeout on attempt {}/{}. Retrying in {} seconds...'.format(
                        attempt + 1, max_retries + 1, retry_delay), xbmc.LOGWARNING)
                time.sleep(retry_delay)
                retry_delay *= 2
                continue
            else:
                theerror = {'error': 'Request timed out after {} attempts'.format(max_retries + 1)}
                if xbmc:
                    xbmc.log('Final timeout error', xbmc.LOGERROR)
                if default is not None:
                    return default
                else:
                    return theerror
                    
        except Exception as e:
            # Catch any other unexpected errors
            error_msg = 'Unexpected error: {}'.format(str(e))
            theerror = {'error': error_msg}
            if xbmc:
                xbmc.log('Unexpected error: {}'.format(error_msg), xbmc.LOGERROR)
            if default is not None:
                return default
            else:
                return theerror
    
    # This should never be reached, but just in case
    if default is not None:
        return default
    else:
        return {'error': 'Maximum retries exceeded'}
