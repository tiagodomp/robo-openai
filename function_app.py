import azure.functions as func
import logging
import os
import azure.cognitiveservices.speech as speechsdk 
import openai
import tempfile
import json

app = func.FunctionApp()

SPEECH_KEY=os.environ.get('SPEECH_KEY','')
SPEECH_REGION=os.environ.get('SPEECH_REGION','eastus2')
SPEECH_ENDPOINT=os.environ.get('SPEECH_ENDPOINT','https://eastus2.api.cognitive.microsoft.com/sts/v1.0/issuetoken')
OPENAI_API_KEY=os.environ.get('OPENAI_API_KEY','')
# Learn more at aka.ms/pythonprogrammingmodel

# Get started by running the following code to create a function using a HTTP trigger.

@app.function_name(name="upload")
@app.route(route="upload")
def main(req: func.HttpRequest) -> func.HttpResponse:
    response = {}

    # speech_file = open("audio.mp3", mode="wb")
    # speech_file.write(req.get_body())
    response = speech_to_text(req.get_body())
    # speech_file.close() #if os.stat(speech_file.name).st_size > 0 else {"error": "Arquivo vazio"}
    # response['success'] = "Liste 3 benefícios de sair do on-premisse para Azure"
    # if 'success' in response:
    #     response = consult_openai(response['success'])
    # response['success'] = "1. Redu\u00e7\u00e3o de custos: Ao migrar suas cargas de trabalho para Azure, \u00e9 poss\u00edvel reduzir os custos de infraestrutura, manuten\u00e7\u00e3o e atualiza\u00e7\u00e3o.\n\n2. Maior escalabilidade: A infraestrutura da nuvem permite que os recursos sejam facilmente escalonados para atender a demandas sazonais ou picos de tr\u00e1fego.\n\n3. Acesso global: Azure oferece uma rede global de data centers, permitindo que empresas tenham acesso a suas aplica\u00e7\u00f5es e dados em qualquer lugar do mundo, inclusive em regi\u00f5es onde a legisla\u00e7\u00e3o de prote\u00e7\u00e3o de dados \u00e9 mais restritiva.\n\n4. Flexibilidade: A infraestrutura da nuvem permite que as empresas tenham mais flexibilidade na escolha de tecnologias, ferramentas e servi\u00e7os, permitindo que elas se adaptem facilmente \u00e0s mudan\u00e7as de demanda ou novas oportunidades de neg\u00f3cios.\n\n5. Maior seguran\u00e7a: Azure oferece recursos avan\u00e7ados de seguran\u00e7a, como autentica\u00e7\u00e3o multifator, criptografia de dados e prote\u00e7\u00e3o contra amea\u00e7as cibern\u00e9ticas, garantindo a prote\u00e7\u00e3o dos dados e das aplica\u00e7\u00f5es.".encode(encoding="utf-8")
    # if 'success' in response:
    #     response = text_to_speech(response['success'])

    # if 'success' in response:    
    #     return func.HttpResponse( response['success'], status_code=200, mimetype='audio/x-wav' )
    
    return func.HttpResponse( json.dumps(response), status_code=200 )

def speech_to_text(audio_file: bytes) -> dict:
    response = {}
    # channels = 1
    # bits_per_sample = 16
    # samples_per_second = 16000
    logging.info("--------------- Start Speech to text -----------------")
    # audio_format = speechsdk.audio.AudioStreamFormat(samples_per_second, bits_per_sample, channels)
    compressed_format = speechsdk.audio.AudioStreamFormat(compressed_stream_format=speechsdk.AudioStreamContainerFormat.MP3)
    custom_push_stream = speechsdk.audio.PushAudioInputStream(stream_format=compressed_format)
    custom_push_stream.write(audio_file)
    logging.info("--------------- Audio salvo -----------------")
    
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, endpoint=SPEECH_ENDPOINT)
    speech_config.speech_recognition_language="pt-BR"
    audio_config = speechsdk.audio.AudioConfig(stream=custom_push_stream)
    logging.info("--------------- Configuração concluída -----------------")
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config, audio_config, language="en-US")
    

    # class BinaryFileReaderCallback(speechsdk.audio.PullAudioInputStreamCallback):
    #     def __init__(self, filename: str):
    #         super().__init__()
    #         self._file_h = open(filename, "rb")

    #     def read(self, buffer: memoryview) -> int:
    #         try:
    #             size = buffer.nbytes
    #             frames = self._file_h.read(size)

    #             buffer[:len(frames)] = frames

    #             return len(frames)
    #         except Exception as ex:
    #             print('Exception in `read`: {}'.format(ex))
    #             raise

    #     def close(self) -> None:
    #         print('closing file')
    #         try:
    #             self._file_h.close()
    #         except Exception as ex:
    #             print('Exception in `close`: {}'.format(ex))
    #             raise
    # # Creates an audio stream format. For an example we are using MP3 compressed file here
    # compressed_format = speechsdk.audio.AudioStreamFormat(compressed_stream_format=speechsdk.AudioStreamContainerFormat.MP3)
    # #callback = BinaryFileReaderCallback(filename='audio.mp3')
    # stream = speechsdk.audio.PushAudioInputStream(stream_format=compressed_format)
    # stream.write(callback.read())

    # speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, endpoint=SPEECH_ENDPOINT)
    # audio_config = speechsdk.audio.AudioConfig(stream=stream)

    # # Creates a speech recognizer using a file as audio input, also specify the speech language
    # speech_recognizer = speechsdk.SpeechRecognizer(speech_config, audio_config)

    # speech_recognition_result = speech_recognizer.recognize_once_async().get()
    
    speech_recognition_result = speech_recognizer.recognize_once()

    logging.info("--------------- Audio processado -----------------")
    logging.info("---------- {} ------------".format(speech_recognition_result.reason))
    if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
        response['success'] = speech_recognition_result.text
    elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
        response['not_recognized'] = speech_recognition_result.no_match_details
    elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_recognition_result.cancellation_details
        response = {
            'canceled': cancellation_details.reason,
            'error': cancellation_details.error_details if cancellation_details.error_details else  "Cancelado: ".format(speech_recognition_result.reason)
        }
    else:
        response['error'] = "Erro desconhecido: ".format(speech_recognition_result.reason)

    logging.info("response: {}".format(json.dumps(response)))
    logging.info("___________________________________________")    
    custom_push_stream.close()

    return response

def consult_openai(text: str) -> dict:
    response = {}
    openai.api_key = OPENAI_API_KEY

    logging.info("--------------- Start OpenAI -----------------")
    try:
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": text}])
        response['success'] = completion.choices[0].message.content
    except openai.OpenAIError as e:
        response['error'] = e.error

    logging.info("response: {}".format(json.dumps(response)))    
    logging.info("___________________________________________")  
    return response

def text_to_speech(text: str) -> dict:
    response = {}
    channels = 1
    bits_per_sample = 16
    samples_per_second = 16000
    audio_format = speechsdk.audio.AudioStreamFormat(samples_per_second, bits_per_sample, channels)
    
    logging.info("--------------- Start text to speech -----------------")
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, endpoint=SPEECH_ENDPOINT)
    # with tempfile.NamedTemporaryFile(suffix='.mp3') as audio_file:
    audio_config = speechsdk.audio.AudioOutputConfig(stream=audio_format)
    
    logging.info("--------------- Configurado Saída de audio -----------------")
    speech_config.speech_synthesis_voice_name='pt-BR-AntonioNeural'
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    logging.info("--------------- Sintetizador Configurado -----------------")
                                                #.speak_ssml_async(ssml).get()
    speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()
    logging.info("--------------- Texto processado -----------------")
    logging.info("---------- {} ------------".format(speech_synthesis_result.reason))

    if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        response['success'] = speech_synthesis_result.audio_data
    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        response['canceled'] = cancellation_details.reason
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                response['error']['value'] = cancellation_details.error_details
                response['error']['text'] = "Chave ou Região definida inválida!"
    else:
        response['error'] = "Error desconhecido"
        
    logging.info("response: {}".format(json.dumps(response)))    
    logging.info("___________________________________________")  
    return response