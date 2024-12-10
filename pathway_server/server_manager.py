import os
import time
import config
import requests

TIME_PERIOD = 5
BASE_DATA_DIRECTORY = config.BASE_DATA_DIRECTORY
FAST_SERVER_DATA_DIRECTORY = config.FAST_VECTOR_STORE_DATA_DIR
SLOW1_SERVER_DATA_DIRECTORY = config.SLOW1_VECTOR_STORE_DATA_DIR
SLOW2_SERVER_DATA_DIRECTORY = config.SLOW2_VECTOR_STORE_DATA_DIR
FAST_SERVER_CACHE_DIRECTORY = config.FAST_VECTOR_STORE_CACHE_DIR
SLOW1_SERVER_CACHE_DIRECTORY = config.SLOW1_VECTOR_STORE_CACHE_DIR
SLOW2_SERVER_CACHE_DIRECTORY = config.SLOW2_VECTOR_STORE_CACHE_DIR
FAST_SERVER_URL = (
    f"http://{config.FAST_VECTOR_STORE_HOST}:{config.FAST_VECTOR_STORE_PORT}"
)
SLOW1_SERVER_URL = (
    f"http://{config.SLOW1_VECTOR_STORE_HOST}:{config.SLOW1_VECTOR_STORE_PORT}"
)
SLOW2_SERVER_URL = (
    f"http://{config.SLOW2_VECTOR_STORE_HOST}:{config.SLOW2_VECTOR_STORE_PORT}"
)

LOGINFO = 0
LOGDEBUG = 1
LOGWARN = 2
LOGERROR = 3
LOG_LEVEL = LOGINFO


def log(level, message):
    if level >= LOG_LEVEL:
        if level == LOGINFO:
            print(f"[INFO] {message}")
        elif level == LOGDEBUG:
            print(f"[DEBUG] {message}")
        elif level == LOGWARN:
            print(f"[WARN] {message}")
        elif level == LOGERROR:
            print(f"[ERROR] {message}")


"""
Check if the server is up and running
Hits the /v1/statistics endpoint of the server
If the server is up, it returns True
If the server is down, it returns False
"""


def check_server_status(url):
    stat_url = url + "/v1/statistics"
    try:
        response = requests.post(
            stat_url,
            json={},
            headers={"Content-Type": "application/json"},
            timeout=2,
        )
        responses = response.json()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


"""
Get the status of all the servers
"""


def get_all_server_status():
    return (
        check_server_status(FAST_SERVER_URL),
        check_server_status(SLOW1_SERVER_URL),
        check_server_status(SLOW2_SERVER_URL),
    )


added_to_slow1 = False  # Flag to check if the file is added to slow1
file_added_to_slow1 = None  # File added to slow1
added_to_slow2 = False  # Flag to check if the file is added to slow2
file_added_to_slow2 = None  # File added to slow2

"""
Manage the servers
Should be called in a loop
"""


def manage(past_base_data_directory):

    global added_to_slow1
    global added_to_slow2
    global file_added_to_slow1
    global file_added_to_slow2

    fast_server_status, slow1_server_status, slow2_server_status = (
        get_all_server_status()
    )

    curr_base_data_directory = os.listdir(BASE_DATA_DIRECTORY)
    curr_fast_data_directory = os.listdir(FAST_SERVER_DATA_DIRECTORY)
    curr_slow1_data_directory = os.listdir(SLOW1_SERVER_DATA_DIRECTORY)
    curr_slow2_data_directory = os.listdir(SLOW2_SERVER_DATA_DIRECTORY)

    fast_data_directory_pending = list(
        set(curr_base_data_directory) - set(curr_fast_data_directory)
    )
    slow1_data_directory_pending = list(
        set(curr_base_data_directory) - set(curr_slow1_data_directory)
    )
    slow2_data_directory_pending = list(
        set(curr_base_data_directory) - set(curr_slow2_data_directory)
    )

    if fast_server_status:
        log(LOGINFO, f"Fast server is up")

        if len(fast_data_directory_pending) > 0:
            log(LOGINFO, "Fast server has pending files")

            # Link the file to the fast server
            # This is a hard link
            file = fast_data_directory_pending[0]
            os.link(
                os.path.join(BASE_DATA_DIRECTORY, file),
                os.path.join(FAST_SERVER_DATA_DIRECTORY, file),
            )

            log(LOGINFO, f"File {file} is linked to fast server")
        else:
            log(LOGINFO, "Fast server has no pending files")
    else:
        log(LOGINFO, f"Fast server is down")

    if not slow1_server_status:
        log(LOGINFO, f"Slow1 server is down")

    if not slow2_server_status:
        log(LOGINFO, f"Slow2 server is down")

    if slow1_server_status and slow2_server_status:
        log(LOGINFO, f"Both Slow1 and Slow2 servers are up")

        if added_to_slow1 and added_to_slow2:
            log(LOGERROR, "Added to both")

        # Slow1 is up and running
        # Indexing is also done
        # Transfer the slow1 cache to slow2
        # Link the file to slow2 as well
        if added_to_slow1:
            log(LOGINFO, "Copying cache of Slow1 to Slow2")
            os.system(
                f"cp -ruT {SLOW1_SERVER_CACHE_DIRECTORY} {SLOW2_SERVER_CACHE_DIRECTORY}"
            )
            os.link(
                os.path.join(BASE_DATA_DIRECTORY, file_added_to_slow1),
                os.path.join(SLOW2_SERVER_DATA_DIRECTORY, file_added_to_slow1),
            )
            added_to_slow1 = False
            file_added_to_slow1 = None

        # redundant code
        # never used
        elif added_to_slow2:
            log(LOGINFO, "Copying cache of Slow2 to Slow1")
            os.system(
                f"cp -ruT {SLOW2_SERVER_CACHE_DIRECTORY} {SLOW1_SERVER_CACHE_DIRECTORY}"
            )
            os.link(
                os.path.join(BASE_DATA_DIRECTORY, file_added_to_slow2),
                os.path.join(SLOW1_SERVER_DATA_DIRECTORY, file_added_to_slow2),
            )
            added_to_slow2 = False
            file_added_to_slow2 = None

        # Slow1 and Slow2 are up and running
        # Check if the data directories are consistent
        # If not consistent, log an error
        # If consistent, link the file to the slow1 server if pending
        # SLow1 will go down if file is linked
        elif not added_to_slow1 and not added_to_slow2:
            diff_of_slow1_slow2_data = list(
                set(curr_slow1_data_directory) - set(curr_slow2_data_directory)
            )

            if len(diff_of_slow1_slow2_data) > 0:
                log(LOGERROR, "Slow1 and Slow2 data directories inconsistent")

            if len(slow1_data_directory_pending) > 0:
                log(LOGINFO, "Slow1 server has pending files")
                file = slow1_data_directory_pending[0]
                os.link(
                    os.path.join(BASE_DATA_DIRECTORY, file),
                    os.path.join(SLOW1_SERVER_DATA_DIRECTORY, file),
                )
                added_to_slow1 = True
                file_added_to_slow1 = file
                log(LOGINFO, f"File {file} is linked to slow1 server")
            else:
                log(LOGINFO, "Slow1 server has no pending files")
        else:
            log(LOGERROR, "This should not happen")


if __name__ == "__main__":
    print("Server Manager started")

    past_base_data_directory = os.listdir(BASE_DATA_DIRECTORY)

    while True:
        manage(past_base_data_directory=past_base_data_directory)
        time.sleep(TIME_PERIOD)
