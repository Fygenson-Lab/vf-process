# ---------------------------------------------------------------------------------------------------- #
#
#   generate_aggregate.csv
#
# ---------------------------------------------------------------------------------------------------- #
#
#   -------------------------------------------------------
#   Development History & Contacts  |
#   --------------------------------|----------------------
#   Principal Investigator          |    Deborah Fygenson
#   Project Guidance                |    Thomas Reese
#   make_aggregate_csv.py           |    Tyler Frischknecht
#   -------------------------------------------------------
#   Last Updated: 7/15/2026
#
# ---------------------------------------------------------------------------------------------------- #
import numpy
import os
import pandas
# ---------------------------------------------------------------------------------------------------- #
# GLOBAL VARIABLES
#                  = [R"~Documents/nanostar/concentration_folder", ...]
PARENT_DIRECTORIES = [

]

# HEADERS FROM ANALYSIS & ASSIGNMENT CSV FILES
VOLUME_FRACTION_HEADER =    "dense_volume_fraction"
A_HEADER =                  "a_ds_psf"
B_HEADER =                  "b_ds_psf"
DILUTE_RADIUS_HEADER =      "dilute_radius_nearest_neighbor"
DENSE_RADIUS_HEADER =       "dense_radius_ds_psf"
DROP_INCLUDE_HEADER =       "include"
# ---------------------------------------------------------------------------------------------------- #
#
#   UTILITY FUNCTIONS
#
# ---------------------------------------------------------------------------------------------------- #
def calculateMeanAndSE(Column_Data : numpy.ndarray) -> tuple[float, float]:
    '''
    # calculateMeanAndSE

    Calculates the mean and standard error of a single numpy ndarray.

    Parameters
    ----------
    `Column_Data` : *numpy.ndarray*
        - The array data being analyzed. Represents a single column of a DataFrame or table.

    Returns
    -------
    *float*
        - The calculated mean.
    *float*
        - The calculated standard error.

    Examples
    --------
    >>> data = numpy.ndarray([0, 1, 2, 3, 4])
    >>> mean, standard_error = calculateMeanAndSE(data)
    >>> print(f"Mean: {mean:.4f}, Standard Error: {standard_error:.4f}})
    Mean: 2.0000, Standard Error: 0.7071
    '''
    Column_Data = Column_Data[numpy.isfinite(Column_Data)] # filtering NaN and inf
    value_count = int(Column_Data.size)
    if value_count < 1:
        return numpy.nan, numpy.nan
    mean = float(numpy.mean(Column_Data))
    standard_error = float(numpy.std(Column_Data, ddof = 0) / numpy.sqrt(value_count))
    return (mean, standard_error)
# -------------------------------------------------- #
def readCsvRows(
    Csv_Path : os.PathLike | str,
    Skip_Rows_Upper : int = 0,
    Skip_Rows_Lower : int = 0,
) -> pandas.DataFrame:
    '''
    # readCsvRows

    Returns a pandas dataframe of all rows within the range:
    (0+Skip_Rows_Upper, Max-Skip_Rows_Lower)

    Parameters
    ----------
    `Csv_Path` : *os.PathLike* | *str*
        - Path of the CSV to populate a pandas dataframe with.
    `Skip_Rows_Upper` : *int*
        - Number of rows from the top to exclude. '0' skips no rows.
    `Skip_Rows_Lower` : *int*
        - Number of rows from the bottom to exclude. '0' skips no rows.

    Returns
    -------
    *pandas.DataFrame*
        - DataFrame generated from read_csv with skipped rows. Shaped like passed .csv

    Examples
    --------
    >>> data_frame = readCsvRows('logs/table1.csv')
    >>> data_frame = readCsvRows('logs/table1.csv', Skip_Rows_Upper = 5, Skip_Rows_Lower = 5)
    '''

    if not os.path.exists(Csv_Path):
        return pandas.DataFrame()

    try:
        kwargs = {
            'skiprows' : Skip_Rows_Upper, 
            'low_memory' : False,
        }
        if Skip_Rows_Lower > 0:
            kwargs['skipfooter'] = Skip_Rows_Lower
            kwargs['engine'] = 'python'
        return pandas.read_csv(Csv_Path, **kwargs)
    except:
        return pandas.DataFrame()
# ---------------------------------------------------------------------------------------------------- #
#
#   Aggregate CSV Generation
#
# ---------------------------------------------------------------------------------------------------- #
def createAggregateCsv(
    Parent_Directory : os.PathLike | str,
    Volume_Fraction_Header : str =  VOLUME_FRACTION_HEADER,
    A_Header : str =                A_HEADER,
    B_Header : str =                B_HEADER,
    Dilute_Radius_Header : str =    DILUTE_RADIUS_HEADER,
    Dense_Radius_Header : str =     DENSE_RADIUS_HEADER,
    Drop_Include_Header : str =     DROP_INCLUDE_HEADER,
    Output_Location : str =         "aggregate.csv",
    Output_Absolute_Path : bool =   False
) -> None:
    '''
    # createAggregateCsv

    Generates an aggregate log of average values across all analysis logs. Each row corresponds \
    with the average data of one analysis log. If a filter was run on analysis logs, only drops \
    marked '1' in a filter column will be processed into aggregate.csv

    Parameters
    ----------
    `Parent_Directory` : *os.PathLike* | *str*
        - Points to a single concentration directory.
    `Volume_Fraction_Header` : *str*, optional
        - Header name for volume fraction in an analysis log.
    `A_Header` : *str*, optional
        - Header name for the first fitting parameter of the double sphere function in an \
        analysis log. Used for A/B ratios. 
    `B_Header` : *str*, optional
        - Header name for the second fitting parameter of the double sphere function in an \
        analysis log. Used for A/B ratios. 
    `Dilute_Radius_Header` : *str*, optional
        - Header name for dilute radius in an analysis log. Used for volume fraction calculation.
    `Dense_Radius_Header` : *str*, optional
        - Header name for dense radius in an analysis log. Used for volume fraction calculation.
    `Drop_Include_Header` : *str*, optional
        - Header name for a filter column. Any drops not marked '1' will not be incorporated in \
        aggregate calculations.
    `Output_Location` : *str*, optional
        - Name for the aggregate csv generated, to be placed in ~/logs/<Output_Location>, unless \
        Output_Absolute_Path is True.
    `Output_Absolute_Path` : *bool*, optional
        - When True, treats Output_Location as an absolute path, and does not route to \
        ~/logs/<Output_Location>
    
    Returns
    -------
    *None*
        - createAggregateCsv returns no values. A CSV file is generated at the passed target path.

    Examples
    --------
    >>> createAggregateCsv('nanostar/concentration_folder')
    '''

    logs_directory = os.path.join(Parent_Directory, 'logs')
    analysis_logs_directory = os.path.join(logs_directory, 'analysis_logs')
    
    if not os.path.exists(logs_directory):
        raise FileNotFoundError(f"Missing analysis_logs directory: {logs_directory}")
    if not os.path.exists(analysis_logs_directory):
        raise FileNotFoundError(f"Missing analysis_logs directory: {analysis_logs_directory}")
        
    all_analysis_logs_paths = sorted([
        os.path.join(analysis_logs_directory, file_name)
        for file_name in os.listdir(analysis_logs_directory)
        if (
            os.path.isfile(os.path.join(analysis_logs_directory, file_name)) and 
            not file_name.startswith('.')
        )
    ])

    output_rows = []

    for file_path in all_analysis_logs_paths:
        data_frame = readCsvRows(file_path)

        if (
            Volume_Fraction_Header not in data_frame.columns or
            A_Header not in data_frame.columns or
            B_Header not in data_frame.columns or
            Dilute_Radius_Header not in data_frame.columns or
            Dense_Radius_Header not in data_frame.columns
        ):
            print("Required header(s) missing from " + file_path)
            continue

        row_count = int(data_frame.shape[0])
            
        if Drop_Include_Header in data_frame.columns:
            data_frame = data_frame.loc[data_frame[Drop_Include_Header] == 1]

        passing_filter_count = int(data_frame.shape[0])

        if data_frame.empty:
            output_rows.append([
                os.path.basename(file_path),
                numpy.nan, numpy.nan,
                numpy.nan, numpy.nan,
                numpy.nan, numpy.nan,
                numpy.nan, numpy.nan,
                0,
                row_count,
            ])
            continue

        all_a_over_b = (
            data_frame[A_Header].astype(float).to_numpy() /
            data_frame[B_Header].astype(float).to_numpy()
        )
      
        output_rows.append([
            os.path.basename(file_path),
            *calculateMeanAndSE(data_frame[Volume_Fraction_Header].astype(float).to_numpy()),
            *calculateMeanAndSE(all_a_over_b),
            *calculateMeanAndSE(data_frame[Dilute_Radius_Header].astype(float).to_numpy()),
            *calculateMeanAndSE(data_frame[Dense_Radius_Header].astype(float).to_numpy()),
            passing_filter_count,
            row_count
        ])

    headers_list = [
        "source_file",
        "avg_dense_volume_fraction",    "volume_fraction_std_err",
        "average_a_over_b",             "a_over_b_std_err",
        "average_dilute_radius",        "dilute_radius_std_err",
        "average_dense_radius",         "dense_radius_std_err",
        "drops_passing_filter",
        "total_drop_count",
    ]

    output_path = Output_Location if Output_Absolute_Path else os.path.join(logs_directory, Output_Location)
    output_dataframe = pandas.DataFrame(
        output_rows,
        columns = headers_list,
    )

    output_dataframe.to_csv(output_path, index = False)
# ---------------------------------------------------------------------------------------------------- #
#
#   MAIN
#
# ---------------------------------------------------------------------------------------------------- #
def main() -> None:
    for parent_directory in PARENT_DIRECTORIES:
        if not os.path.exists(os.path.join(parent_directory, 'logs')):
            print("Skipping invalid directory: ", parent_directory)
            continue
        createAggregateCsv(parent_directory)
        print("Successfully created aggregate.csv for ", os.path.join(parent_directory))
# -------------------------------------------------- #
if __name__ == "__main__":
    main()
# ---------------------------------------------------------------------------------------------------- #
