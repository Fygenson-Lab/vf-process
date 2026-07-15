# ----------------------------------------------------------------------------------------------- #
#
#   generate_frame_times.py
#
# ----------------------------------------------------------------------------------------------- #
#
#   -------------------------------------------------------
#   Development History & Contacts  |
#   --------------------------------|----------------------
#   Principal Investigator          |    Deborah Fygenson
#   Project Guidance                |    Thomas Reese
#   frame_time_linker.py            |    Tyler Frischknecht
#   -------------------------------------------------------
#   Last Updated: 7/15/2026
#
# ----------------------------------------------------------------------------------------------- #
#
#   Creates .csv log correlating each movie frame with a timestamp and delay column.
#   <parent>/movie/movie.tif is a required file. This script reads the metadata of the multipage
#   tiff itself to generate <parent>/logs/frame_times.csv
#
# ----------------------------------------------------------------------------------------------- #
from numpy import nan as numpy_nan
import os
import pandas
import tifffile
# ----------------------------------------------------------------------------------------------- #
#
#   GLOBAL VARIABLES
#
# ----------------------------------------------------------------------------------------------- #
#                  = [R"~/nanostar/concentration_folder", ...]
PARENT_DIRECTORIES = [

]

LOGS_SUBDIRECTORY =     'logs'
MOVIE_SUBDIRECTORY =    'movie/movie.tif'
# ----------------------------------------------------------------------------------------------- #
#
#   UTILITY FUNCTIONS
#
# ----------------------------------------------------------------------------------------------- #
def createFrameTimeCSV(
    Movie_Path : os.PathLike | str, 
    Logs_Path : os.PathLike | str, 
    Output_Location : str = "frame_times.csv",
    Output_Absolute_Path : bool = False
) -> None:
    '''
    # createFrameTimeCSV

    Generates a CSV of frames indices, time elapsed, and time since the previous frame.

    Parameters
    ----------
    `Movie_Path` : *os.PathLike* | *str*
        - Path to the multipage movie tiff.
    `Logs_Path` : *os.PathLike* | *str*
        - Path to the logs directory, where /analysis_logs is present. 
    `Output_Location` : *str*, optional
        - Name for the frame time csv generated, to be placed in ~/logs/<Output_Location>, unless \
        Output_Absolute_Path is True.
    `Output_Absolute_Path` : *bool*, optional
        - When True, treats Output_Location as an absolute path, and does not route to \
        ~/logs/<Output_Location>

    Returns
    -------
    *None*
        - No values are returned from createFrameTimeCSV

    Examples
    --------
    >>> createFrameTimeCSV('movie/movie.tif', 'concentration/logs')
    >>> createFrameTimeCSV(
    ...     'movie/movie.tif', 
    ...     'concentration/logs', 
    ...     '~/concentration/logs/named_file.csv', 
    ...     True
    ... )
    '''

    output_csv_rows = []

    with tifffile.TiffFile(Movie_Path) as tiff_data:
        for frame_index in range(len(tiff_data.pages)):
            if frame_index < 0 or frame_index >= len(tiff_data.pages):
                print(f"frame_index: {frame_index} out of range")
                output_csv_rows.append([frame_index, numpy_nan, numpy_nan])
                continue

            time_from_start, time_from_last = getFrameTime(
                tiff_data.pages[frame_index].tags.get("ImageDescription")
            )

            output_csv_rows.append([frame_index, time_from_start, time_from_last])

    if not Output_Absolute_Path:
        Output_Location = os.path.join(Logs_Path, Output_Location)

    csv_dataframe = pandas.DataFrame(output_csv_rows, columns = ["frame", "time_from_start", "time_from_last"])

    csv_dataframe.to_csv(Output_Location, index = False)
# -------------------------------------------------- #
def getFrameTime(
    Metadata : tifffile.TiffTag, 
) -> tuple[float, float]:
    '''
    # getFrameTime

    Reads the metadata of a single frame of a multipage tiff, returning the time since the \
    previous frame, and the total time elapsed.

    Parameters
    ----------
    `Metadata` : *tifffile.TiffTag*
        - The ImageDescription metadata of a single frame.

    Returns
    -------
    *float*
        - The time elapsed at this frame. Returns -1 if no metadata found.
    *float*
        - The time from the previous frame. Returns -1 if no metadata found.

    Examples
    --------
    >>> time_from_start, time_from_last = getFrameTime(metadata)
    '''

    if not Metadata:
        return -1, -1 # No metadata available
    
    # Stores metadata as string
    text = Metadata.value

    # Parse metadata string for time data
    time_from_start = None
    time_from_last = None

    for line in text.splitlines():
        line = line.strip()
        if line.startswith("Time_From_Start"):
            _, value = line.split('=')
            time_from_start = parseTimeString(value.strip())
            print(line, "\t", time_from_start)
        elif line.startswith("Time_From_Last"):
            _, value = line.split('=')
            time_from_last = parseTimeString(value.strip())
            print(line, "\t", time_from_last)

    return time_from_start, time_from_last
# -------------------------------------------------- #
def parseTimeString(Time_Str : str) -> float:
    '''
    # parseTimeString

    Parses a string in the form HH:MM:SS.SS, returning a single time value in seconds.

    Parameters
    ----------
    `Time_Str` : *str*
        - The string to parse.

    Returns
    -------
    *float*
        - The timestamp converted to a float in seconds.

    Examples
    --------
    >>> time = parseTimeString('54:32:10.98')
    >>> print(f"{time:.2f}")
    196330.98
    '''

    hours, minutes, seconds = Time_Str.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
# ----------------------------------------------------------------------------------------------- #
#
#   MAIN
#
# ----------------------------------------------------------------------------------------------- #
def main() -> None:
    successful = 0
    total = len(PARENT_DIRECTORIES)
    for directory in PARENT_DIRECTORIES:
        try:
            MOVIE_PATH = os.path.join(directory, MOVIE_SUBDIRECTORY)
            LOGS_PATH = os.path.join(directory, LOGS_SUBDIRECTORY)

            print("Validating pathways...")

            if not os.path.isfile(MOVIE_PATH):
                raise FileNotFoundError(f"Movie file not found: {MOVIE_PATH}")
            if not os.path.isdir(LOGS_PATH):
                raise FileNotFoundError(f"Logs directory not found: {LOGS_PATH}")
            
            print("Generating CSV...")
            createFrameTimeCSV(MOVIE_PATH, LOGS_PATH)
            successful += 1
        except:
            print("Failed to generate csv for: ", directory)
    print(f"Generated frame_time CSV files for {successful}/{total} directories.")
# -------------------------------------------------- #
if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------------------------- #