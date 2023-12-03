import argparse
import wave
from pathlib import Path
from secrets import compare_digest

# remember to install ffmpeg (sudo apt install ffmpeg)
from pydub import AudioSegment

import numpy as np
from PIL import Image

salt = "P@$$1"


def get_file_extension(path):
    p = Path(path)
    return p.name.split(".")[1]


def convert_jpg_to_png(jpg_path):
    p = Path(jpg_path)
    png_path = "{}.png".format(p.stem)
    jpg = Image.open(jpg_path)
    jpg.save(png_path)
    return png_path


def convert_mp3_to_wav(mp3_path):
    p = Path(mp3_path)
    wav_path = "{}.wav".format(p.stem)
    mp3 = AudioSegment.from_mp3(mp3_path)
    mp3.export(wav_path, format="wav")
    return wav_path


def convert_string_to_binary(text):
    # convert each text in string to the ascii equivalent
    ascii_text_list = []
    for i in text:
        ascii_text_list.append(ord(i))
    # convert each ascii representation to binary
    binary_text_list = []
    for i in ascii_text_list:
        binary_text_list.append(format(i, "08b"))

    return binary_text_list


def convert_binary_to_string(binary):
    return chr(int(binary, 2))


def encode_image_message(text, image_src):
    img = Image.open(image_src, "r")
    width, height = img.size
    # convert image to array of pixels
    pixel_list = np.array(list(img.getdata()))
    # compute the total number of pixels
    n = len(img.mode)
    pixel_count = pixel_list.size // n
    # convert the text to a list of binary representation
    message_in_binary = "".join(convert_string_to_binary(text + salt))
    # compute the total number of binary representations for each character in text
    bit_count = len(message_in_binary)

    if bit_count > pixel_count:
        print(
            "Message to be encoded is too large for image. Use a bigger image or shrink the message to be encrypted"
        )
    else:
        # run a 2d loop to loop through the pixels and the rgb channels of each pixel
        index = 0
        for p in range(pixel_count):
            for q in range(0, 3):
                if index < bit_count:
                    try:
                        # convert the pixel channel to binary and add a bit from the message
                        pixel_list[p][q] = int(
                            bin(pixel_list[p][q])[2:9] + message_in_binary[index], 2
                        )
                        index += 1
                    except:
                        print(
                            "an error occurred. ensure you are not trying on a transparent png"
                        )

    # convert the updated pixel list to the new image and save
    pixel_list = pixel_list.reshape(height, width, n)
    encoded_image = Image.fromarray(pixel_list.astype("uint8"), img.mode)
    p = Path(image_src)
    encoded_image.save("{}_encoded.png".format(p.stem))
    print("Image encode complete. Location @ {}_encoded.png".format(p.stem))


def decode_image_message(image_src):
    if get_file_extension(image_src) == "png":
        img = Image.open(image_src, "r")
    else:
        return print("only png is supported for decrypt")

    pixel_list = np.array(list(img.getdata()))

    n = len(img.mode)

    pixel_count = pixel_list.size // n

    binary_sequence = ""
    for p in range(pixel_count):
        for q in range(0, 3):
            # remove the last bit from the binary representation of the pixel and add to the sequence
            binary_sequence += bin(pixel_list[p][q])[2:][-1]

    binary_list = []
    # in batches of 8(utf8) append them to a list for conversion to text
    for i in range(0, len(binary_sequence), 8):
        binary_list.append(binary_sequence[i : i + 8])

    text = ""
    # for each batch convert and append to build text string
    for item in binary_list:
        # if our salt is discovered in the image then we have gotten the complete text message so we can end
        if compare_digest(text[-5:], salt):
            break
        else:
            # keep building the text message until we discover the salt
            text += convert_binary_to_string(item)

    # if we found the salt in text then return the message
    if salt in text:
        print("Encrypted Message is = ", text[:-5])
    else:
        print("No Encrypted Message in Image")


def encode_audio_message(text, audio_src):
    # check the format of file passed

    if get_file_extension(audio_src) == "mp3":
        wav_path = convert_mp3_to_wav(audio_src)
        audio_src = wav_path
        wav = wave.open(audio_src, "rb")
    elif get_file_extension(audio_src) == "wav":
        wav = wave.open(audio_src, "rb")
    else:
        return print("only mp3 or wav is supported")

    wav_bytes = wav.readframes(-1)

    wav_byte_list = bytearray(list(wav_bytes))

    byte_count = len(wav_byte_list)

    # convert the text to a list of binary representation
    message_in_binary = "".join(convert_string_to_binary(text + salt))

    # compute the total number of binary representations for each character in text
    bit_count = len(message_in_binary)

    if bit_count > byte_count:
        print(
            "Message to be encoded is too large for audio. Use a bigger audio file or shrink the message to be encrypted"
        )
    else:
        index = 0
        for b in range(byte_count):
            if index < bit_count:
                try:
                    # convert the music int to binary and add a bit from the message
                    wav_byte_list[b] = (wav_byte_list[b] & 254) | int(
                        message_in_binary[index]
                    )
                    index += 1
                except:
                    print("an error occurred while parsing through your media")

    # generate new audio file
    p = Path(audio_src)
    encoded_audio = wave.open("{}_encoded.wav".format(p.stem), "wb")
    encoded_audio.setparams(wav.getparams())
    encoded_audio.writeframes(bytes(wav_byte_list))
    wav.close()


def decode_audio_message(audio_src):
    if get_file_extension(audio_src) == "wav":
        wav = wave.open(audio_src, "rb")
    else:
        return print("only wav is supported for decrypt")

    wav_bytes = wav.readframes(-1)

    wav_byte_list = bytearray(list(wav_bytes))

    byte_count = len(wav_byte_list)

    binary_sequence = ""

    for p in range(byte_count):
        # remove the last bit from the binary representation of the pixel and add to the sequence
        binary_sequence += bin(wav_byte_list[p])[2:][-1]

    binary_list = []
    # in batches of 8(utf8) append them to a list for conversion to text
    for i in range(0, len(binary_sequence), 8):
        binary_list.append(binary_sequence[i : i + 8])

    text = ""
    # for each batch convert and append to build text string
    for item in binary_list:
        # if our salt is discovered in the image then we have gotten the complete text message so we can end
        if compare_digest(text[-5:], salt):
            break
        else:
            # keep building the text message until we discover the salt
            text += convert_binary_to_string(item)

    # if we found the salt in text then return the message
    if salt in text:
        print("Encrypted Message is = ", text[:-5])
    else:
        print("No Encrypted Message in Image")
    wav.close()


def main():
    parser = argparse.ArgumentParser(
        prog="PySteg",
        description="Steganography powered by python",
        epilog="Built by ifeanyi.ibekie@gmail.com for CS50. Note that it may create new files for compatibility issues with mp3 and jpg. Also only encoded files from this application can be decoded by this software.",
        add_help=True,
    )
    parser.add_argument("mode", help="encode/decode")
    parser.add_argument(
        "-i",
        "--image",
        help="jpg/png file path for encoding, png file path only for decoding",
    )
    parser.add_argument(
        "-s",
        "--sound",
        help="mp3/wav file path for encoding, wav file path only for decoding",
    )
    parser.add_argument("-t", "--text", help="text for encoding mode only")

    args = parser.parse_args()

    print("Operation Initialized")

    if args.mode == "encode" and args.image is not None and args.text is not None:
        encode_image_message(args.text, args.image)
    elif args.mode == "decode" and args.image is not None:
        decode_image_message(args.image)
    elif args.mode == "encode" and args.sound is not None and args.text is not None:
        encode_audio_message(args.text, args.sound)
    elif args.mode == "decode" and args.sound is not None:
        decode_audio_message(args.sound)
    else:
        print("run -h to understand how to use this application")

    print("Operation Completed")


if __name__ == "__main__":
    main()
