from flask import Flask, request, redirect, Response
from flask_cors import CORS
import requests
import config
import json
import pandas as pd


app = Flask(__name__)
CORS(app)

CSV_FILENAME = "endpoints.csv"


def getURL(x, y, operation):

    current_operations, current_names, current_endpoints = read_csv()

    # Default to add in order to catch errors
    if operation is None or operation == "":
        index = search("+", current_operations)
        url = current_endpoints[index]
        final_url = f"{url}?x={x}&y={y}"

    else:
        # ensure valid operation was passed
        if operation in current_operations:
            index = search(operation, current_operations)
            url = current_endpoints[index]
            final_url = f"{url}?x={x}&y={y}"

    return final_url


def search(operation, current_operations):
    for i in range(len(current_operations)):
        if current_operations[i] == operation:
            return i


@app.route("/")
def proxy():
    x = request.args.get("x")
    y = request.args.get("y")
    operation = request.args.get("operation")

    # Dont check for x or y since endpoints do this
    if operation is None or operation == "":
        invalid_return = {"error": True, "string": "Param 'operation' is missing"}
        reply = json.dumps(invalid_return)
        r = Response(response=reply, status=200, mimetype="application/json")
        r.headers["Content-Type"] = "application/json"
        r.headers["Access-Control-Allow-Origin"] = "*"
        return r

    # remove whitespace
    operation = operation.strip()

    url = getURL(x, y, operation)

    print(url)

    resp = requests.get(f"{url}")

    if resp.status_code != 200:
        invalid_return = {"error": True, "string": f"Endpoint returned status {resp.status_code}"}
        reply = json.dumps(invalid_return)
        r = Response(response=reply, status=200, mimetype="application/json")
        r.headers["Content-Type"] = "application/json"
        r.headers["Access-Control-Allow-Origin"] = "*"
        return r

    excluded_headers = [
        "content-encoding",
        "content-length",
        "transfer-encoding",
        "connection",
    ]

    headers = [
        (name, value)
        for (name, value) in resp.raw.headers.items()
        if name.lower() not in excluded_headers
    ]

    r = Response(resp.content, resp.status_code, headers)
    r.headers["Content-Type"] = "application/json"
    r.headers["Access-Control-Allow-Origin"] = "*"
    return r


# add operation
@app.route("/add")
def add_operation():
    operation = request.args.get("operation")
    name = request.args.get("name")
    endpoint = request.args.get("endpoint")

    if operation is None or operation == "":
        invalid_return = {"error": True, "string": "Param 'operation' is missing"}
        reply = json.dumps(invalid_return)
        r = Response(response=reply, status=200, mimetype="application/json")
        r.headers["Content-Type"] = "application/json"
        r.headers["Access-Control-Allow-Origin"] = "*"
        return r
    if name is None or name == "":
        invalid_return = {"error": True, "string": "Param 'name' is missing"}
        reply = json.dumps(invalid_return)
        r = Response(response=reply, status=200, mimetype="application/json")
        r.headers["Content-Type"] = "application/json"
        r.headers["Access-Control-Allow-Origin"] = "*"
        return r
    if endpoint is None or endpoint == "":
        invalid_return = {"error": True, "string": "Param 'endpoint' is missing"}
        reply = json.dumps(invalid_return)
        r = Response(response=reply, status=200, mimetype="application/json")
        r.headers["Content-Type"] = "application/json"
        r.headers["Access-Control-Allow-Origin"] = "*"
        return r

    # remove whitespace
    operation = operation.strip()
    name = name.strip()
    endpoint = endpoint.strip()

    current_operations, current_names, current_endpoints = read_csv()

    # add trailing slash
    if endpoint[-1:] != "/":
        endpoint = f"{endpoint}/"

    if operation in current_operations:
        invalid_return = {
            "error": True,
            "string": f"Operation {operation} already exists. Did you mean to update?",
        }
        reply = json.dumps(invalid_return)
        r = Response(response=reply, status=200, mimetype="application/json")
        r.headers["Content-Type"] = "application/json"
        r.headers["Access-Control-Allow-Origin"] = "*"
        return r
    if name in current_names:
        invalid_return = {
            "error": True,
            "string": f"Operation {name} already exists. Did you mean to update?",
        }
        reply = json.dumps(invalid_return)
        r = Response(response=reply, status=200, mimetype="application/json")
        r.headers["Content-Type"] = "application/json"
        r.headers["Access-Control-Allow-Origin"] = "*"
        return r
    if endpoint in current_endpoints:
        invalid_return = {
            "error": True,
            "string": f"Endpoint {endpoint} already exists. Did you mean to update?",
        }
        reply = json.dumps(invalid_return)
        r = Response(response=reply, status=200, mimetype="application/json")
        r.headers["Content-Type"] = "application/json"
        r.headers["Access-Control-Allow-Origin"] = "*"
        return r

    # Try making a request to ensure endpoint is valid
    resp = requests.get(endpoint)
    try:
        # check status 200
        status = resp.status_code
        if status != 200:
            invalid_return = {
                "error": True,
                "string": f"Endpoint returned status code {status}",
            }
            reply = json.dumps(invalid_return)
            r = Response(response=reply, status=200, mimetype="application/json")
            r.headers["Content-Type"] = "application/json"
            r.headers["Access-Control-Allow-Origin"] = "*"
            return r

        # check error is present. ensures
        error = resp.json().get("error")

    except Exception:
        invalid_return = {
            "error": True,
            "string": f"Endpoint {endpoint} could not be connected to.",
        }
        reply = json.dumps(invalid_return)
        r = Response(response=reply, status=200, mimetype="application/json")
        r.headers["Content-Type"] = "application/json"
        r.headers["Access-Control-Allow-Origin"] = "*"
        return r

    try:
        append_to_csv(f"\n{operation},{name},{endpoint}")
    except:
        invalid_return = {
            "error": True,
            "string": f"Failed to update config with {name} ({operation}) operation with endpoint '{endpoint}'",
        }
        reply = json.dumps(invalid_return)
        r = Response(response=reply, status=200, mimetype="application/json")
        r.headers["Content-Type"] = "application/json"
        r.headers["Access-Control-Allow-Origin"] = "*"
        return r

    valid_return = {
        "error": False,
        "string": f"{operation}:{name}: successfully added with endpoint {endpoint}",
    }
    reply = json.dumps(valid_return)
    r = Response(response=reply, status=200, mimetype="application/json")
    r.headers["Content-Type"] = "application/json"
    r.headers["Access-Control-Allow-Origin"] = "*"
    return r


# update operation
@app.route("/update")
def update_endpoint():
    operation_name = request.args.get("name")
    new_endpoint = request.args.get("endpoint")

    if operation_name is None or operation_name == "":
        invalid_return = {"error": True, "string": "Param 'name' is missing"}
        reply = json.dumps(invalid_return)
        r = Response(response=reply, status=200, mimetype="application/json")
        r.headers["Content-Type"] = "application/json"
        r.headers["Access-Control-Allow-Origin"] = "*"
        return r
    if new_endpoint is None or new_endpoint == "":
        invalid_return = {"error": True, "string": "Param 'endpoint' is missing"}
        reply = json.dumps(invalid_return)
        r = Response(response=reply, status=200, mimetype="application/json")
        r.headers["Content-Type"] = "application/json"
        r.headers["Access-Control-Allow-Origin"] = "*"
        return r

    # remove whitespace
    operation_name = operation_name.strip()
    new_endpoint = new_endpoint.strip()

    current_operations, current_names, current_endpoints = read_csv()

    # add trailing slash
    if new_endpoint[-1:] != "/":
        new_endpoint = f"{new_endpoint}/"

    if operation_name not in current_names:
        invalid_return = {
            "error": True,
            "string": f"Operation {operation_name} does not exist. Did you mean to add?",
        }
        reply = json.dumps(invalid_return)
        r = Response(response=reply, status=200, mimetype="application/json")
        r.headers["Content-Type"] = "application/json"
        r.headers["Access-Control-Allow-Origin"] = "*"
        return r

    # Try making a request to ensure new endpoint is valid
    resp = requests.get(new_endpoint)
    try:
        # check status 200
        status = resp.status_code
        if status != 200:
            invalid_return = {
                "error": True,
                "string": f"Endpoint returned status code {status}",
            }
            reply = json.dumps(invalid_return)
            r = Response(response=reply, status=200, mimetype="application/json")
            r.headers["Content-Type"] = "application/json"
            r.headers["Access-Control-Allow-Origin"] = "*"
            return r

        # check error is present. ensures
        error = resp.json().get("error")

    except Exception:
        invalid_return = {
            "error": True,
            "string": f"Endpoint {new_endpoint} could not be connected to.",
        }
        reply = json.dumps(invalid_return)
        r = Response(response=reply, status=200, mimetype="application/json")
        r.headers["Content-Type"] = "application/json"
        r.headers["Access-Control-Allow-Origin"] = "*"
        return r

    try:
        if (
            update_csv(
                current_operations,
                current_names,
                current_endpoints,
                operation_name,
                new_endpoint,
            )
            != True
        ):
            invalid_return = {
                "error": True,
                "string": f"'{new_endpoint}' Endpoint already exists for {operation_name} operation",
            }
            reply = json.dumps(invalid_return)
            r = Response(response=reply, status=200, mimetype="application/json")
            r.headers["Content-Type"] = "application/json"
            r.headers["Access-Control-Allow-Origin"] = "*"
            return r

    except:
        invalid_return = {
            "error": True,
            "string": f"Failed to update config with {operation_name} operation with new endpoint '{new_endpoint}'",
        }
        reply = json.dumps(invalid_return)
        r = Response(response=reply, status=200, mimetype="application/json")
        r.headers["Content-Type"] = "application/json"
        r.headers["Access-Control-Allow-Origin"] = "*"
        return r

    valid_return = {
        "error": False,
        "string": f"{operation_name}: successfully updated with new endpoint {new_endpoint}",
    }
    reply = json.dumps(valid_return)
    r = Response(response=reply, status=200, mimetype="application/json")
    r.headers["Content-Type"] = "application/json"
    r.headers["Access-Control-Allow-Origin"] = "*"
    return r


# delete operation
@app.route("/delete")
def delete_endpoint():
    operation_name = request.args.get("name")

    if operation_name is None or operation_name == "":
        invalid_return = {"error": True, "string": "Param 'name' is missing"}
        reply = json.dumps(invalid_return)
        r = Response(response=reply, status=200, mimetype="application/json")
        r.headers["Content-Type"] = "application/json"
        r.headers["Access-Control-Allow-Origin"] = "*"
        return r

    # remove whitespace
    operation_name = operation_name.strip()

    operations, names, endpoints = read_csv()

    if operation_name not in names:
        invalid_return = {
            "error": True,
            "string": f"Operation {operation_name} does not exist. Did you mean to add?",
        }
        reply = json.dumps(invalid_return)
        r = Response(response=reply, status=200, mimetype="application/json")
        r.headers["Content-Type"] = "application/json"
        r.headers["Access-Control-Allow-Origin"] = "*"
        return r

    try:
        csv_remove_endpoint = "Operation,Name,Endpoint"

        for i in range(len(names)):
            if names[i] != operation_name:
                csv_remove_endpoint += f"\n{operations[i]},{names[i]},{endpoints[i]}"

        write_to_csv(csv_remove_endpoint)

    except:
        invalid_return = {
            "error": True,
            "string": f"Failed to delete {operation_name} from config",
        }
        reply = json.dumps(invalid_return)
        r = Response(response=reply, status=200, mimetype="application/json")
        r.headers["Content-Type"] = "application/json"
        r.headers["Access-Control-Allow-Origin"] = "*"
        return r

    valid_return = {
        "error": False,
        "string": f"Successfully deleted {operation_name} endpoint.",
    }
    reply = json.dumps(valid_return)
    r = Response(response=reply, status=200, mimetype="application/json")
    r.headers["Content-Type"] = "application/json"
    r.headers["Access-Control-Allow-Origin"] = "*"
    return r


# view endpoints
@app.route("/view")
def view_endpoints():
    current_operations, current_names, current_endpoints = read_csv()
    reply = "<b>Current Endpoints:</b><br/><br/>"

    for i in range(len(current_operations)):
        reply += f"{current_operations[i]} ({current_names[i]}): {current_endpoints[i]}<br/><br/>"

    r = Response(response=reply, status=200)
    r.headers["Access-Control-Allow-Origin"] = "*"
    return r


def read_csv():
    print("Reading Data from CSV File")
    df = pd.read_csv(CSV_FILENAME)

    # get ids and values and add to list
    operations = df["Operation"].tolist()
    names = df["Name"].tolist()
    endpoints = df["Endpoint"].tolist()

    return operations, names, endpoints


def write_to_csv(lines_to_write):
    file = open(CSV_FILENAME, "w")
    file.writelines(lines_to_write)
    file.close()
    print("Successfully wrote to csv file")


def update_csv(operations, names, endpoints, operation_name, new_endpoint):
    updated_operations = ["Operation,Name,Endpoint"]
    csv_updated = False

    for i in range(len(names)):
        if names[i] == operation_name:
            if endpoints[i] != new_endpoint:
                endpoints[i] = new_endpoint
                csv_updated = True

        updated_operations.append(f"\n{operations[i]},{names[i]},{endpoints[i]}")

    write_to_csv(updated_operations)
    updated_operations.clear()

    return csv_updated


def append_to_csv(data_to_append):
    with open(CSV_FILENAME, "a") as csv_file:
        csv_file.write(data_to_append)
    print("Successfully appended to csv file")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
