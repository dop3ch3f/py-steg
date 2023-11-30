mod util;

use clap::{Error, Parser};
use crate::util::write_to_terminal_multicolor;


use std::fs::File;
use std::io::BufReader;
use std::io::prelude::*;
use std::path::Path;
use std::fs;
use std::io::Cursor;
use image::io::Reader as ImageReader;
use image::Pixel;


/// Simple program to decode and encode steganography images
#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// mode of operation (encode decode)
    #[arg(short ="m", long="mode", default_value_t = "encode")]
    mode: Option<String>,

    /// input image file (to encode, to decode)
    #[arg(short = "i", long = "input")]
    input_path: Option<String>,

    /// encode text (text to be encoded in image)
    #[arg(short = "t", long = "text")]
    text: Option<String>,
}

fn encode(args: Args) -> Result<(), dyn std::error::Error> {
    let Some(mode) = args.mode.as_deref();
    let Some(text) = args.text.as_deref();
    let Some(input_path) = args.input_path.as_deref();

    // we check inputs needed for input
    if mode == "encode" {
        let path = Path::new(input_path);
        if (path.try_exists()?) {
            let img = ImageReader::open(path)?.decode()?;
            let img_clone = img.clone();
            let mut input_bytes = img_clone.to_rgba8().as_raw();
            let mut text_bytes = text.as_bytes();

            write_to_terminal_multicolor("text bytes start")?;
            for byte in text_bytes {
                println!("{}", byte);
            }
            write_to_terminal_multicolor("text bytes end")?;

            // we need to ensure that the image is bigger than the input text
            if (input_bytes.len()  > (text_bytes.len() * 8)) {
                let mut input_pixels = img_clone.to_rgba8().pixels_mut();
                // loop over each pixel in the image
                for pixel in input_pixels {
                    let channels = pixel.channels_mut();
                    for channel in 0..channels {
                        println!("{}", channel)
                    }
                }
                // generate the output path
                let mut output = format!("{}-output.{}", path.file_name().as_deref()?.to_str()?, path.extension().as_deref()?.to_str()? );
                // if the output path exists delete it and replace
                let output_path = Path::new(output.as_str());
                if (output_path.try_exists()?) {
                    fs::remove_file(output_path)?;
                }
                let mut output_image =  ImageReader::new(img_clone).with_guessed_format()?.decode()?;
                output_image.save(output_path)?;
            }

            panic!("Image needs to be atleast 8 times bigger than the data to be hidden");
        } else {
            panic!("Input file doesn't exist")
        }
    }

    Ok(())
}

fn decode(args: Args) -> Result<(), dyn std::error::Error> {
    Ok(())
}


fn main() -> std::io::Result<()> {
    let args = Args::parse();

    write_to_terminal_multicolor(
        "Rust Steg\nIfeanyi Ibekie <ifeanyi.ibekie@gmail.com>\nHarness the power of steganography\n"
    )?;

    match String::from(args.mode).as_str() {
        "encode" => {
            encode(args.clone())?;
            Ok(())
        }
        "decode" => {
            decode(args.clone())?;
            Ok(())
        }
        _ => {
            write_to_terminal_multicolor(
                "No mode chosen exiting... (try running --help to view list of available modes)",
            )?;
            Ok(())
        }
    }
}
