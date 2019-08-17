# This day extracts a heavy toll.
import os
import sys
import datetime
import pprint
import requests

BASE_URL = 'https://dev.virtualearth.net/REST/v1/Routes/DistanceMatrix'

COORD_FILE = 'sample-input.txt'  # The main coordinate input
TIME_FILE = 'times.txt'  # Specifies the times of the day you need data for. 
API_KEY_FILE = 'keys.txt'  # This file holds your API keys.
PROGRAM_SAVED_STATE = 'state.txt'  # This file saves the program state so it can resume later.

# Specify the particular date you want here:
DAY = 5
MONTH = 8
YEAR = 2019

# Specify Your Timezone
TZ = '-07:00'

def prepare_coordinates(coordinate_lines):
    lines = []
    for line in coordinate_lines:
        split = line.split()
        if not split:
            continue
        coords = '{},{}'.format(split[1], split[2])
        lines.append((split[0], coords))
    return lines


def get_coord_indices(coords):
    d = {}
    for tup in coords:
        d[tup[1]] = tup[0]
    return d


def get_distance_matrix(origin_str, dest_str, date, start_time, api_keys, key_index):
    '''
    Returns a tuple containing the json response from the API call,
    the integer index of the API key used in the call from the api_keys array,
    and a boolean indicating if all API keys have been exhausted (They all give error codes)
    '''
    formated_date = '{}-{}-{}'.format(YEAR, MONTH, DAY)
    request_accepted = False
    all_keys_finished = False
    params = dict(
        origins=origin_str,
        destinations=dest_str,
        distanceUnit='mi',
        travelMode='driving',
        startTime='{}T{}{}'.format(formated_date, start_time, TZ),
        key=api_keys[key_index],
    )
    # print(params)
    r = requests.get(url=BASE_URL, params=params)
    data = r.json()
    request_accepted = data['statusCode'] == 200

    while not request_accepted:
        key_index += 1
        if key_index == len(api_keys):
            # We have tried all keys, and they're giving errors
            all_keys_finished = True
            break
        params['key'] = api_keys[key_index]
        r = requests.get(url=BASE_URL, params=params)
        data = r.json()
        request_accepted = data['statusCode'] == 200
    # pprint.pprint(data, width=1)
    return data, key_index, all_keys_finished


def parse_results(data, coord_to_index):
    parsed = []
    destinations =  data['resourceSets'][0]['resources'][0]['destinations']
    origins = data['resourceSets'][0]['resources'][0]['origins']
    results = data['resourceSets'][0]['resources'][0]['results']

    for cell in results:
        try:
            d = destinations[cell['destinationIndex']]
            dest = '{},{}'.format(d['latitude'], d['longitude'])
            orig = origins[cell['originIndex']]
            origin = '{},{}'.format(orig['latitude'], orig['longitude'])
            res = {
                'dest_index': coord_to_index[dest],
                'origin_index': coord_to_index[origin],
                'travel_duration': str(cell['travelDuration']),
                'walk_duration': str(cell['totalWalkDuration']),
                'travel_distance': str(cell['travelDistance'])
            }
            parsed.append(res)
            # print('Done {} to {}'.format(res['origin_index'], res['dest_index']))
        except:
            continue
    return parsed


def read_input_list(file_name):
    with open(file_name, 'r') as fin:
        lines = [line.strip() for line in fin.readlines()]
    return lines


def save_program_state(i, j, time, key_index):
    with open(PROGRAM_SAVED_STATE, 'w+') as fout:
        fout.write(str(i) + '\n')
        fout.write(str(j) + '\n')
        fout.write(str(time) + '\n')
        fout.write(str(key_index) + '\n')


def join_coords(coords):
    return ';'.join([tup[1] for tup in coords])


def write_rows(api_data, date, time):
    output_path = 'output.txt'
    headers = '   '.join(['OriginIndex', 'DestinationIndex', ' Date', 'Time',
                'TravelDistance', 'TravelDuration'])
    with open(output_path, 'a+') as fout:
        if os.stat(output_path).st_size == 0:
            fout.write(headers + '\n')
        for data in api_data:
            if data['origin_index'] == data['dest_index']:
                continue
            line = [
                data['origin_index'],
                data['dest_index'],
                date,
                time,
                data['travel_distance'],
                data['travel_duration'],
                '\n'
            ]
            fout.write('   '.join(line))


def calc_batches():
    # REad and prepare our input files.
    times = read_input_list(TIME_FILE)
    api_keys = read_input_list(API_KEY_FILE)
    coords = prepare_coordinates(read_input_list(COORD_FILE))
    coord_to_index = get_coord_indices(coords)
    n = len(coords)

    # Set current date
    date = '{}-{}-{}'.format(DAY, MONTH, YEAR)

    i_resume_index = j_resume_index = time_resume_index = key_index = 0
    has_resumed = False

    # Check if there is data saved to continue API calls from where they left off.
    if os.path.exists(PROGRAM_SAVED_STATE):
        print('Retrieving Saved State....')
        state_values = read_input_list(PROGRAM_SAVED_STATE)
        print(state_values)
        if len(state_values) == 4:
            i_resume_index = int(state_values[0]) - 1
            j_resume_index = int(state_values[1])
            time_resume_index = int(state_values[2])
            key_index = int(state_values[3])

    # Bing API only allows us to send 10 or less cells as input
    # This means we can send a 3 x 3 matrix or origin and destination,
    # or a 5 x 2, etc. I chose 1 x 9 matrix.
    i_step, j_step = 1, 9

    print('Starting from origin {} and destination {} and time {}'.format(
        i_resume_index + 1, j_resume_index, times[time_resume_index])
    )
    j = j_resume_index

    # The main loop logic.
    for t_index in range(time_resume_index, len(times)):
        time = times[t_index]
        for i in range(i_resume_index, n, i_step):
            
            if j_resume_index != 0 and has_resumed:
                j = 0
            if j_resume_index != 0 or i_resume_index != 0:
                has_resumed = True
            while j < n:
                y_start, y_end = i, i + i_step
                x_start, x_end = j, j + j_step
                # print(y_start, y_end, x_start, x_end, time)
                origins = join_coords(coords[y_start: y_end])
                destinations = join_coords(coords[x_start: x_end])
                data, key_index, all_keys_finished = get_distance_matrix(
                    origins,
                    destinations,
                    date,
                    time,
                    api_keys,
                    key_index
                )
                if all_keys_finished:
                    msg1 = 'All API keys are returning errors. You have likely exhausted\
                          your daily rates.'
                    print(msg1)

                    # Reset key_index, so that next time we start trying API keys again from the
                    # beginning.
                    key_index = 0
                    save_program_state(i, j, t_index, key_index)
                    sys.exit('Saving program state and exiting...')
                api_data = parse_results(data, coord_to_index)
                write_rows(api_data, date, time)
                # print('{} {} {} {}'.format(y_end, x_end, t_index, key_index))
                print(y_end, x_end)
                save_program_state(y_end, x_end, t_index, key_index)
                
                j += j_step


    print('Finished processing input!')
    try:
        os.remove(PROGRAM_SAVED_STATE)
    except OSError:
        pass


if __name__ == '__main__':
    calc_batches()