# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

import argparse
import logging
import subprocess
import time

import numpy as np
import thorlabs_apt as apt
import settings

MOVING_DISTANCE = 0.1

def run_init_settings():
    logging.info("adb root")
    process = subprocess.run(["adb", "root"], stdout=subprocess.PIPE)
    setup_cmds = settings.shield_settings

    for cmd in setup_cmds:
        logging.info(cmd)
        process = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
        logging.debug(process.stdout.decode("utf8"))


def get_motors():
    m1, m2 = apt.list_available_devices()
    logging.info(f"Motor 1: {m1}")
    logging.info(f"Motor 2: {m2}")
    x = apt.Motor(m2[1])
    y = apt.Motor(m1[1])

    return x, y


def collect_data(samples=50):
    # Clear logcat
    process = subprocess.run(["adb", "shell", "logcat", "-c"], stdout=subprocess.PIPE)
    # run mcuservice to collect proximity sensor data
    process = subprocess.Popen(
        ["adb", "shell", "mfg", "captouch", "status", "10"], stdout=subprocess.PIPE)

    data = []
    current_sample = 0
    # parse data for 8 config values
    for line in process.stdout:
        if "DIFF_825c_mean" in line.decode("utf8").strip():
            line = line.decode("utf8").strip()
            line = line.strip(',')
            adc_config = line.split(": ")
            data.append(adc_config[-1])
            current_sample += 1
            if current_sample >= samples:
                logging.info(f"{samples} have been collected.")
                process.kill()
                break
    process.wait()
    return data

def run_motor_seq(motor, step=0.1, iterations=65):
    logging.info(f"Motor position: {motor.position}mm")

    adc_data = collect_data()
    logging.info(adc_data)

    #get_config_ave(adc_data)

    for _index in range(iterations):
        motor.move_by(MOVING_DISTANCE)
        while True:
            if motor.is_in_motion is False:
                logging.info(f"Motor position: {motor.position}mm")
                break

        adc_data = collect_data()
        logging.info(adc_data)
       # get_config_ave(adc_data)


def main():

    log_formatter = logging.Formatter(
        "%(asctime)s [%(threadName)s] [%(levelname)s]  %(message)s"
    )

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    filename = "proxtest"
    file_handler = logging.FileHandler(f"{filename}.log")
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    parser = argparse.ArgumentParser(description="Proximity Sensor Threshold Test")
    parser.add_argument(
        "-i",
        "--init",
        type=bool,
        metavar="",
        required=False,
        help='Set to "True" if this is the first run after power cycing. If set to "True", the script will run required setup commands.',
    )

    args = parser.parse_args()

    if args.init:
        logging.info("Running init settings...")
        run_init_settings()

    x, y = get_motors()
    time.sleep(2)

    logging.info("Homing x-axis...")
    x.move_home(True)
    while True:
       if x.is_in_motion is False:
           logging.info("X Position: " + str(x.position))
           break

    logging.info("Homing y-axis...")
    y.move_home(True)
    while True:
        if y.is_in_motion is False:
            logging.info("Y Position: " + str(y.position))
            break

    y.move_to(15.5)
    while True:
        if y.is_in_motion is False:
            logging.info("Y Position: " + str(y.position))
            break

    x.move_to(5.6)
    logging.info("X Position: " + str(x.position))
    while True:
        if x.is_in_motion is False:
            logging.info("X Position: " + str(x.position))
            break

    input("please mount the glass")
    run_motor_seq(x)

    input("test complete!")

if __name__ == "__main__":
    main()
