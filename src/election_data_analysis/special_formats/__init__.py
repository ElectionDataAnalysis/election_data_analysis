import pandas as pd
import io
from election_data_analysis import munge as m
from election_data_analysis import juris_and_munger as jm
from election_data_analysis import user_interface as ui


def strip_empties(li: list) -> list:
    # get rid of leading empty strings
    first_useful = next(idx for idx in range(len(li)) if li[idx] != "")
    li = li[first_useful:]

    # get rid of trailing empty strings
    li.reverse()
    first_useful = next(idx for idx in range(len(li)) if li[idx] != "")
    li = li[first_useful:]
    li.reverse()

    return li


def extract_items(line: str, w: int) -> list:
    """assume line ends in \n.
    drops any trailing empty strings from list"""
    item_list = [
        line[idx * w : (idx + 1) * w].strip() for idx in range(int((len(line) - 1) / w))
    ]
    item_list = strip_empties(item_list)
    return item_list


def read_concatenated_blocks(
    f_path: str, munger: jm.Munger, err: dict
) -> (pd.DataFrame, dict):
    """Assumes first column of each block is ReportingUnit, last column is contest total"""
    try:
        with open(f_path, "r") as f:
            data = f.readlines()
    except Exception as exc:
        err = ui.add_error(err, "datafile_error", f"Datafile not read:\n{exc}")
        return pd.DataFrame(), err

    # get  munger parameters
    w = munger.options["column_width"]
    tlts = munger.options["count_of_top_lines_to_skip"]
    v_t_cc = munger.options["last_header_column_count"]
    skip_cols = munger.options["columns_to_skip"]

    df = dict()

    # skip lines at top
    data = data[tlts:]

    try:
        while len(data) > 3:
            # TODO allow number & interps of headers to vary?
            # get rid of blank lines
            while data[0] == "\n":
                data.pop(0)

            # get the header lines
            header_0 = data.pop(0).strip()
            header_1 = data.pop(0)
            header_line = data.pop(0)

            # get info from header line
            field_list = extract_items(header_line, w)
            last_header = field_list[1 : 1 + v_t_cc]
            if (len(field_list) - len(skip_cols) - 1) % v_t_cc != 0:
                e = f"Count of last header ({v_t_cc}) does not evenly divide the number of count columns ({len(field_list) - len(skip_cols) - 1})"
                ui.add_error(err,"munge_error",e)
                return pd.DataFrame(), err

            header_1_list = extract_items(header_1, w * v_t_cc)

            # create df from next batch of lines, with that multi-index
            # find idx of next empty line (or end of data)
            try:
                next_empty = next(idx for idx in range(len(data)) if data[idx] == "\n")
            except StopIteration:
                next_empty = len(data)
            # create io
            vote_count_block = io.StringIO()
            vote_count_block.write("".join(data[:next_empty]))
            vote_count_block.seek(0)

            df[header_0] = pd.read_fwf(
                vote_count_block, colspecs="infer", index=False, header=None
            )

            # Drop extraneous columns (per munger). Negative numbers count from right side
            df[header_0].drop(df[header_0].columns[skip_cols], axis=1, inplace=True)

            # make first column into an index
            df[header_0].set_index(keys=[0], inplace=True)

            # add multi-index with header_1 and header_2 info
            index_array = [
                [y for z in [[cand] * v_t_cc for cand in header_1_list] for y in z],
                last_header * len(header_1_list),
            ]
            df[header_0].columns = pd.MultiIndex.from_arrays(index_array)

            # move header_1 & header_2 info to columns
            df[header_0] = pd.melt(
                df[header_0],
                ignore_index=False,
                value_vars=df[header_0].columns.tolist(),
                value_name="count",
                var_name=["header_1", "header_2"],
            )

            # Add columns for header_0
            df[header_0] = m.add_constant_column(df[header_0], "header_0", header_0)

            # remove processed lines from data
            data = data[next_empty:]
    except Exception as exc:
        err = ui.add_error(
            err, "datafile_warning", f"unparsed lines at bottom of file:\n{data}"
        )

    # consolidate all into one dataframe
    try:
        raw_results = pd.concat(list(df.values()))
    except ValueError as e:
        err = ui.add_error(
            err,"datafile_error",f"Error concatenating data from blocks: {e}"
        )
        return pd.DataFrame, err

    # Make row index (from first column of blocks) into a column called 'first_column'
    raw_results.reset_index(inplace=True)
    raw_results.rename(columns={0: "first_column"}, inplace=True)

    return raw_results, err