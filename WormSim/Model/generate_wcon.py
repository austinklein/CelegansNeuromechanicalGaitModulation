import numpy as np
import time
import os
import math
import json

MICROMETERS_PER_MILLIMETER = 1e3

def generate_wcon(time_arr, x_arr, y_arr, d_arr, original_file_name, center_x_arr, center_y_arr, radius_arr, wcon_file_name):
    assert(x_arr.shape == y_arr.shape)
    assert(time_arr.size == x_arr.shape[1])

    num_steps = time_arr.size

    n_bar = x_arr.shape[0]
    n_seg = int(n_bar - 1)
    r = 40e-3

    r_i = np.array([
        r * abs(math.sin(math.acos(((i) - n_seg / 2.0) / (n_seg / 2.0 + 0.2))))
        for i in range(n_bar)
    ]).reshape(-1, 1)

    dx = np.cos(d_arr)*r_i
    dy = np.sin(d_arr)*r_i

    px = np.zeros((2*n_bar, x_arr.shape[1]))
    py = np.zeros((2*n_bar, x_arr.shape[1]))

    px[:n_bar, :] = x_arr - dx
    px[n_bar:, :] = np.flipud(x_arr + dx) # Make perimeter counter-clockwise

    py[:n_bar, :] = y_arr - dy
    py[n_bar:, :] = np.flipud(y_arr + dy) # Make perimeter counter-clockwise

    timestamp_str = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
    info = "Loaded: %s points from %s, saving %i frames" % (num_steps, original_file_name, num_steps)
    time_arr_list = time_arr.tolist()
    x_arr_list = x_arr.T.tolist()
    y_arr_list = y_arr.T.tolist()
    px_arr_list = px.T.tolist()
    py_arr_list = py.T.tolist()
    ptail = n_bar

    center_x_arr_list = center_x_arr.tolist()
    center_y_arr_list = center_y_arr.tolist()
    radius_arr_list = radius_arr.tolist()

    wcon_dict = {
        "metadata": {
            "who": "CelegansNeuromechanicalGaitModulation",
            "timestamp": timestamp_str,
            "protocol": "Generated by CelegansNeuromechanicalGaitModulation!"
        },
        "units": {
            "t": "s",
            "x": "mm",
            "y": "mm",
            "px": "mm",
            "py": "mm",
        },
        "comment": "Saved from CelegansNeuromechanicalGaitModulation data.",
        "note": info,
        "@CelegansNeuromechanicalGaitModulation": {
            "objects": {
                "circles": {
                    "x": center_x_arr_list,
                    "y": center_y_arr_list,
                    "r": radius_arr_list
                }
            }
        },
        "data": [
            {
                "id": "wormTest",
                "t": time_arr_list,
                "x": x_arr_list,
                "y": y_arr_list,
                "px": px_arr_list,
                "py": py_arr_list,
                "ptail": ptail
            }
        ]
    }

    with open(wcon_file_name, 'w') as wcon_file:
        json.dump(wcon_dict, wcon_file, indent=4)

    print("Generated WCON file: %s"%wcon_file_name)

def validate(wcon_file):
    import json, jsonschema

    wcon_schema = "wcon_schema.json"

    if not os.path.isfile("wcon_schema.json"):
        print("Cannot validate file: %s!! WCON schema %s not found!!"%(wcon_file, wcon_schema))
        return

    # The WCON schema
    with open(wcon_schema, "r") as wcon_schema_file:
        schema = json.loads(wcon_schema_file.read())

    # Our example WCON file
    with open(wcon_file, 'r') as infile:
        serialized_data = infile.read()

    # Load the whole JSON file into a nested dict.
    w = json.loads(serialized_data)

    # Validate the raw file against the WCON schema
    jsonschema.validate(w, schema)

    print("File %s is valid WCON!!"%wcon_file)


if __name__ == "__main__":

    import sys
    pos_file_name = "simdata.csv" if len(sys.argv)<2 else sys.argv[1]

    data = np.genfromtxt(pos_file_name, delimiter=",").T
    ts = data[0]

    x_offset = 1
    y_offset = 2
    d_offset = 3

    x_slice = data[x_offset::3][:]*MICROMETERS_PER_MILLIMETER
    y_slice = data[y_offset::3][:]*MICROMETERS_PER_MILLIMETER
    d_slice = data[d_offset::3][:]

    wcon_file_name = pos_file_name.replace('.csv','.wcon')

    obj_file_name = "objects.csv"
    objects = np.genfromtxt(obj_file_name, delimiter=",")
    obj_center_x = objects[:, 0]*MICROMETERS_PER_MILLIMETER
    obj_center_y = objects[:, 1]*MICROMETERS_PER_MILLIMETER
    obj_radius = objects[:, 2]*MICROMETERS_PER_MILLIMETER

    generate_wcon(ts, x_slice, y_slice, d_slice, pos_file_name, obj_center_x, obj_center_y, obj_radius, wcon_file_name)
    validate(wcon_file_name) 
