"""
    mss.tutorials.audio
    ~~~~~~~~~~~~~~~~~~~

    This python script is meant for generating audio of our choice from text files describing the tuutorial.

    This file is part of mss.

    :copyright: Copyright 2021 Hrithik Kumar Verma
    :copyright: Copyright 2021 by the mss team, see AUTHORS.
    :license: APACHE-2.0, see LICENSE for details.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
import os
import time
import playsound
import googletrans as gt
from gtts import gTTS
from glob import glob


class TutorialAudio:
    """
        This is the audio class for storing audio files and playing them.
    """
    def __init__(self):
        """
            The constructor sets the translator object and audio path for storing the audios.
        """
        self.translate = gt.Translator()
        self.audio_path = os.path.join(os.getcwd(), "Audio Files")
        os.makedirs(self.audio_path, exist_ok=True)

    def translate_text(self, input_text, input_lang, output_lang):
        """
        This function is used to translate texts packets in the output language passed to the function.
        """
        txt = self.translate.translate(input_text, src=input_lang, dest=output_lang)
        return txt.text

    def text_to_audio(self, source_lang, destination_lang):
        """
        This function is used to convert text file into speech of selected choice passed as parameter and store the
        audio files and playing them. It converts all text files one by one present in the textfiles folder.
        """
        for f in glob("textfiles/*.txt"):
            print(f"\nINFO : Please wait, the text file {f} is being converted to audio file...\n")
            with open(f) as file:
                source_text = file.read()
                if source_lang == destination_lang:
                    destination_text = source_text
                else:
                    destination_text = self.translate_text(source_text, source_lang, destination_lang)
                destination_speech = gTTS(destination_text, lang=destination_lang, tld="com", slow=False)
            pathstring = os.path.splitext(f)[0]
            pathstring_list = pathstring.split("/")
            audio_file = pathstring_list[len(pathstring_list) - 1] + f"_{destination_lang}_" + ".mp3"
            destination_speech.save(os.path.join(self.audio_path, audio_file))
            print(f"\n\nINFO : Converted the text file {f} into audio file successfully!\n\n")

        for f in glob(f"{self.audio_path}/*.mp3"):
            try:
                print(f"\nPlaying {f}........\n")
                playsound.playsound(f)
                print(f".\n.\n.\n.\nFinished Playing the {f} file!")
            except KeyboardInterrupt:
                print("The preview of the mp3 file has been finished.")
            time.sleep(1)


def main():
    audutorial = TutorialAudio()
    # Since the text file is written in english, the input language is english.
    input_lang = 'en'
    # English, French, German respectively in output_languages. We could add more number of languages according
    # to our choice and need in the below list.
    output_languages = ['en', 'fr', 'de']
    # Presently, the output audio stream has been set to German.
    audutorial.text_to_audio(input_lang, output_languages[2])


if __name__ == '__main__':
    main()
