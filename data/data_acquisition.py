import argparse
import time
import numpy as np
import msvcrt  # For non-blocking keyboard input on Windows
import brainflow
from brainflow.board_shim import BoardShim, BrainFlowInputParams, LogLevels, BoardIds
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations


def main():
    # --- BrainFlow Setup --- 
    # You might need to change the Board ID and Serial Port based on your specific Ganglion and OS
    # Check BrainFlow docs for how to find your serial port
    # https://brainflow.readthedocs.io/en/stable/SupportedBoards.html#ganglion
    # Common ports: Linux: /dev/ttyACM0 or similar, Mac: /dev/cu.usbmodem*, Windows: COM*
    parser = argparse.ArgumentParser()
    parser.add_argument('--timeout', type=int, help='timeout for device discovery or connection', required=False, default=15)
    parser.add_argument('--serial-port', type=str, help='serial port', required=True)
    parser.add_argument('--board-id', type=int, help='board id, check docs', required=False, default=BoardIds.GANGLION_BOARD.value)
    parser.add_argument('--log', action='store_true', help='enable brainflow log')
    parser.add_argument('--duration', type=int, help='Duration of the recording in seconds', required=False, default=60)
    parser.add_argument('--output-file', type=str, help='Name of the file to save data (without extension)', required=False, default='eeg_data')
    args = parser.parse_args()

    params = BrainFlowInputParams()
    params.serial_port = args.serial_port
    params.timeout = args.timeout

    if args.log:
        BoardShim.enable_dev_board_logger()
    else:
        BoardShim.set_log_level(LogLevels.LEVEL_OFF)

    REST_MARKER = 1.0
    IMAGERY_MARKER = 2.0

    board = BoardShim(args.board_id, params)

    try:
        print(f"Connecting to board {args.board_id} on port {args.serial_port}...")
        board.prepare_session()
        print("Board Connected. Starting stream...")
        board.start_stream(450000) # Start stream, buffer size recommended by BrainFlow docs

        print(f"\n--- Recording for {args.duration} seconds ---")
        print("Press 'R' to mark START of REST period.")
        print("Press 'I' to mark START of IMAGERY period.")
        print("Press 'Q' to STOP recording early and save.")
        print("---------------------------------------------")
        
        start_time = time.time()
        keep_recording = True

        # --- Data Acquisition Loop with Marker Insertion --- 
        while keep_recording and (time.time() - start_time < args.duration):
            # Check for keyboard input
            if msvcrt.kbhit():
                key = msvcrt.getch().decode('utf-8').lower()
                if key == 'r':
                    print(f"\n{time.time() - start_time:.2f}s: Inserting REST marker ({REST_MARKER})")
                    board.insert_marker(REST_MARKER)
                elif key == 'i':
                    print(f"\n{time.time() - start_time:.2f}s: Inserting IMAGERY marker ({IMAGERY_MARKER})")
                    board.insert_marker(IMAGERY_MARKER)
                elif key == 'q':
                    print("\nStopping recording early (Q pressed).")
                    keep_recording = False
            
            # Small sleep to prevent busy-waiting and allow BrainFlow processing
            time.sleep(0.05) 

        # --- Stop Stream and Get Data --- 
        current_duration = time.time() - start_time
        print(f"\n--- Recording finished after {current_duration:.2f} seconds ---")
        print("Stopping stream...")
        board.stop_stream()
        print("Stream stopped.")

        # Data format: rows are channels, columns are samples
        # https://brainflow.readthedocs.io/en/stable/Examples.html#data-get-methods
        data = board.get_board_data() # Gets all data accumulated in the buffer

        # Check marker channel (useful for debugging)
        marker_channel = BoardShim.get_marker_channel(args.board_id)
        print(f"Marker channel index: {marker_channel}")
        if marker_channel < data.shape[0]:
             markers = data[marker_channel, :]
             print(f"Markers found: {np.unique(markers[markers != 0])}")
        else:
            print("No marker channel found in data.")

        # --- Save Data --- 
        # BrainFlow saves data in CSV format by default
        # First columns are EEG channels, then accel, then other, then timestamp, then marker
        # Check board.get_eeg_channels(args.board_id) etc. for exact layout
        eeg_channels = BoardShim.get_eeg_channels(args.board_id)
        print(f"EEG Channels for board {args.board_id}: {eeg_channels}")
        print(f"Data shape: {data.shape}")

        # Save the raw data
        output_filename_raw = f"{args.output_file}_raw.csv"
        DataFilter.write_file(data, output_filename_raw, 'w') 
        print(f"Raw data saved to {output_filename_raw}")

        # Optional: Save just the EEG data
        # output_filename_eeg = f"{args.output_file}_eeg.csv"
        # eeg_data = data[eeg_channels, :]
        # DataFilter.write_file(eeg_data, output_filename_eeg, 'w')
        # print(f"EEG data saved to {output_filename_eeg}")

        print("Acquisition finished.")

    except brainflow.exit_codes.BrainFlowError as e:
        print(f"BrainFlowError: {e}")
        print("Make sure the Ganglion is paired and the correct serial port is specified.")
        print("You might need to run this script with administrator/sudo privileges.")

    except KeyboardInterrupt:
        print("\nRecording stopped by user (Ctrl+C).")
        # Ensure stream is stopped even if interrupted
        if board.is_prepared():
            try:
                board.stop_stream()
                print("Stream stopped.")
                # Optionally save data collected so far
                # data = board.get_board_data()
                # if data.shape[1] > 0:
                #     output_filename_interrupted = f"{args.output_file}_interrupted.csv"
                #     DataFilter.write_file(data, output_filename_interrupted, 'w')
                #     print(f"Partial data saved to {output_filename_interrupted}")
            except brainflow.exit_codes.BrainFlowError as e:
                print(f"Error stopping stream after interrupt: {e}")

    finally:
        # --- Release Session --- 
        if board.is_prepared():
            print("Releasing session...")
            board.release_session()
            print("Session released.")


if __name__ == "__main__":
    main()
