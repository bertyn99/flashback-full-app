import os
from pysrt import SubRipFile
import datetime
import subprocess

# Paths
base_path = os.path.dirname(__file__)
srt_path = os.path.join(base_path, "transcript.srt")
audio_path = os.path.join(base_path, "audio.mp3")
pictures_path = os.path.join(base_path, "pictures")
output_video_path = os.path.join(base_path, "video.mp4")
process_folder = os.path.join(base_path, "process")

# Load subtitles
subtitles = SubRipFile.open(srt_path)

def clean_text(text):
    # Remove unwanted characters
    # text = text.replace('\n', ' ')
    text = text.replace(':', '\\:')
    text = text.replace("'", "`")
    if text.endswith(','):
        text = text[:-1]

    return text

# Generate video segments
segments = []
for subtitle in subtitles:
    start_time = subtitle.start.to_time()
    end_time = subtitle.end.to_time()


    # text = subtitle.text.replace('\n', ' ')
    picture_file = os.path.join(pictures_path, f"{subtitle.index}.png")

    if not os.path.exists(picture_file):
        continue  # Skip if picture does not exist

    # Create video segment with picture and subtitle
    segment_output = os.path.join(process_folder, f"segment_{subtitle.index}.mp4")
    duration = (datetime.datetime.combine(datetime.date.min, end_time) - datetime.datetime.combine(datetime.date.min, start_time)).total_seconds()


    escaped_text = clean_text(subtitle.text)

    print(f"Creating segment {subtitle.index} with duration {duration} seconds")
    # Create video using ffmpeg
    command = [
        'ffmpeg',
        '-loop', '1',
        # '-r', '25',
        # '-pattern_type', 'glob',
        '-i', picture_file,
        '-t', f"{duration}",
        # '-c:v', 'libx264',
        '-tune', 'stillimage',
        '-pix_fmt', 'yuv420p',
        # '-shortest',
        '-vf', f"drawtext=fontfile=font/Helvetica.ttf:text='{escaped_text}':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=(h-text_h)-100",
        segment_output,
        '-y',  # Overwrite output file if it exists
    ]

    subprocess.run(command, check=True)

    # segment = (
    #     ffmpeg.input(picture_file, framerate=25, t=duration).video
    #     .filter("scale", 1080, 1920)
    #     .filter("setsar", 1)
    # )


    # segment = ffmpeg.drawtext(segment, text=text, fontfile="font/Helvetica.ttf", fontsize=36, fontcolor="white", x="(w-text_w)/2", y="h-100", box=1, boxcolor="black@0.5", boxborderw=5)


        # .output(segment_output, vcodec="libx264", pix_fmt="yuv420p") \
        # .run(overwrite_output=True)
    segments.append(segment_output)


#  Store the segments in a temporary file
segments_file = os.path.join(process_folder, "segments.txt")
with open(segments_file, 'w') as f:
    for segment in segments:
        f.write(f"file '{segment}'\n")


# Add audio to the concatenated video
# audio_input = ffmpeg.input(audio_path).audio

# final_video = ffmpeg.concat(*segments, v=1, a=0).output(output_video_path, vcodec="libx264", acodec="aac", audio_bitrate="192k", format="mp4").run(overwrite_output=True)


# Concatenate video segments
command = [
    'ffmpeg',
    '-f', 'concat',
    '-safe', '0',
    '-i', segments_file,
    '-i', audio_path,
    '-c:a', 'aac',
    '-b:a', '192k',
    '-c:v', 'copy',
    '-c:v', 'libx264',
    '-tune', 'stillimage',
    '-pix_fmt', 'yuv420p',
    output_video_path,
    '-y',  # Overwrite output file if it exists
]

subprocess.run(command, check=True)

# Clean up temporary files
for segment in segments:
    os.remove(segment)

os.remove(segments_file)

print(f"Final video saved at {output_video_path}")
