import azure.functions as func
import logging
import os
import azure.cognitiveservices.speech as speechsdk 
import openai
import tempfile
import json

app = func.FunctionApp()

# Learn more at aka.ms/pythonprogrammingmodel

# Get started by running the following code to create a function using a HTTP trigger.

@app.function_name(name="upload")
@app.route(route="upload")
def main(req: func.HttpRequest) -> func.HttpResponse:
    response = {}
    with tempfile.NamedTemporaryFile(suffix=".wav") as speech_file:
        speech_file.write(req.get_body())
        response = speech_to_text(speech_file.name)

    if 'success' in response:
        response = consult_openai(response['success'])

    if 'success' in response:
        response = text_to_speech(response['success'])
        return func.HttpResponse( response['success'], status_code=200, mimetype='audio/x-wav' )
    
    return func.HttpResponse( json.dumps(response), status_code=400 )

def speech_to_text(pathfile: str) -> dict:
    response = {}
    speech_config = speechsdk.SpeechConfig(subscription=os.environ.get('SPEECH_KEY'), region=os.environ.get('SPEECH_REGION'))
    speech_config.speech_recognition_language="pt-BR"

    audio_config = speechsdk.audio.AudioConfig(filename=pathfile)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    speech_recognition_result = speech_recognizer.recognize_once_async().get()

    if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
        response['success'] = speech_recognition_result.text
    elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
        response['not_recognized'] = speech_recognition_result.no_match_details
    elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_recognition_result.cancellation_details
        response['canceled'] = cancellation_details.reason
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            response['error']['value'] = cancellation_details.error_details
            response['error']['text'] = "Chave ou Região definida inválida!"
    else:
        response['error'] = "Erro desconhecido"

    return response

def text_to_speech(text: str) -> dict:
    response = {}
    speech_config = speechsdk.SpeechConfig(subscription=os.environ.get('SPEECH_KEY'), region=os.environ.get('SPEECH_REGION'))
    name_audio = tempfile.NamedTemporaryFile(suffix='.wav').name
    audio_config = speechsdk.audio.AudioOutputConfig(filename=name_audio)

    speech_config.speech_synthesis_voice_name='pt-BR-AntonioNeural'
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
                                                #.speak_ssml_async(ssml).get()
    speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()

    if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        response['success'] = name_audio
    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        response['canceled'] = cancellation_details.reason
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                response['error']['value'] = cancellation_details.error_details
                response['error']['text'] = "Chave ou Região definida inválida!"
    else:
        response['error'] = "Error desconhecido"
    
    return response

def consult_openai(text: str) -> dict:
    response = {}
    openai.api_key = os.environ.get('OPENAI_API_KEY')

    try:
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": text}])
        response['success'] = completion.choices[0].message.content
    except openai.OpenAIError as e:
        response['error'] = e.error