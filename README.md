# prepare the environment 

poetry install

poetry shell

ngrok http 5000

make twilio number and webhook the ngrok url + /answer

# start the flask server

python -m src.app

# start the arize server

docker compose -f docker-compose.arize.yml up

# result

see results after calling twilio number at /call_results

view LLM and prompt information on port 6006
