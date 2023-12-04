import requests, json

SERVER = "http://127.0.0.1"#"https://dialoguesthroughtime.azurewebsites.net"
s = requests.session()
unique_id = s.get(f"{SERVER}/get_unique_id").json()["id"]
print(unique_id)
while True:
    # Assuming you want to make a request to the stream endpoint
    inpt = input("You: ")

    stream_response = s.get(f"{SERVER}/chat?unique_id={unique_id}&user_msg={inpt}&end_conversation={inpt == 'exit'}", stream=True)

    # You should also handle streaming the response here if that's your intent
    try:
        prev_lines = 0
        for line in stream_response.iter_lines():
            if line:
                data_string  = line.decode('utf-8')
                print(data_string,end="\n", flush=True)

                # Remove 'data:' prefix
                if ("data:" in data_string):
                    json_string = data_string.split(":", 1)[1].strip()
                else:
                    json_string = data_string

                # Convert JSON string to dictionary
                data_dict = json.loads(json_string)

                if "ai_speaking" in data_dict:
                    message = "AI: " + data_dict["ai_speaking"]
                    print(message)

    except KeyboardInterrupt:
        # Handling a keyboard interrupt to stop the script
        break
