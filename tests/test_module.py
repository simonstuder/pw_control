
import pw_control.pw_control as PWC
from pprint import pprint
import time
import logging

def test_true()->None:
    assert True

def test_execute_setup()->None:
    logging.basicConfig(level=logging.DEBUG)
    pwc:PWC.PW_Control = PWC.PW_Control(monitorOutput="None")
    assert True

def test_crete_sink()->None:
    test_sink_name:str = "test_sink"
    logging.basicConfig(level=logging.DEBUG)
    pwc:PWC.PW_Control = PWC.PW_Control(monitorOutput="None")

    pwc.delete_all_sinks()
    sinks:list[str] = list(pwc.get_sinks().keys())
    assert test_sink_name not in sinks
    pwc.create_sink(test_sink_name, channels=2,duplicates="ignore",waitForExisting=True)
    sinks:list[str] = list(pwc.get_sinks().keys())
    assert test_sink_name in sinks

def test_delete_all_sinks()->None:
    test_sink_name:str = "test_sink"
    logging.basicConfig(level=logging.DEBUG)
    pwc:PWC.PW_Control = PWC.PW_Control(monitorOutput="None")

    sinks:list[str] = list(pwc.get_sinks().keys())
    pwc.create_sink(test_sink_name, channels=2,duplicates="ignore",waitForExisting=True)
    sinks:list[str] = list(pwc.get_sinks().keys())
    assert test_sink_name in sinks
    pwc.delete_all_sinks()
    assert test_sink_name not in sinks

def all():

    logging.basicConfig(level=logging.DEBUG)

    pwc = PWC.PW_Control(monitorOutput="None")

    pwc.delete_all_sinks()

    sid:int = pwc.create_sink("intermed_sink", channels=2,duplicates="ignore",waitForExisting=True)
    print("_Created Intermediate Sink_\n")

    pwc.disconnect("spotify:output_FL","analog-stereo:playback_FL",raiseOnError=False)
    pwc.disconnect("spotify:output_FR","analog-stereo:playback_FR",raiseOnError=False)
    print("_Disconnected spotify from analog-stereo_\n")

    ss = pwc.get_sinks()
    pprint([ss.keys()])
    pprint(ss)

    pwc.connect("spotify:output_FL","intermed_sink:playback_FL")
    pwc.connect("spotify:output_FR","intermed_sink:playback_FR")
    print("_connected spotify to intermed_sink_\n")

#pwc.connect("intermed_sink:monitor_FL","alsa:pcm:0:front:0:playback:playback_0")
    pwc.connect("intermed_sink:monitor_FR","analog-stereo:playback_FR")
    print("_connected intermed_sink to analog-stere right\n")


if __name__ == "__main__":
    all()


