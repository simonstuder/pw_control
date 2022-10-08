
import pw_control.pw_control as PWC
from pprint import pprint
import logging
from uuid import uuid4
from typing import Any
import pytest

def test_true()->None:
  assert True

@pytest.mark.xfail
def test_false()->None:
  assert False

def test_execute_setup()->None:
  logging.basicConfig(level=logging.DEBUG)
  pwc:PWC.PW_Control = PWC.PW_Control(monitorOutput="None")
  assert not pwc==None

def test_crete_null_sink()->None:
  sink_name:str = f"test_sink_{uuid4()}"
  logging.basicConfig(level=logging.DEBUG)
  pwc:PWC.PW_Control = PWC.PW_Control(monitorOutput="None")

  pwc.delete_all_sinks()
  sinks:dict[str,Any] = pwc.get_sinks()
  assert sink_name not in list(sinks.keys())
  pwc_name:str = pwc.create_null_sink(sink_name, channels=2,duplicates="Exception",waitForExisting=True)
  sinks = pwc.get_sinks()
  assert pwc_name in list(sinks.keys())
  assert pwc_name==sinks[pwc_name]['_pw_control_name']
  assert pwc_name==f"{sink_name}/{sinks[pwc_name]['Properties']['object.serial']}"
  pwc.delete_all_sinks()

def test_create_null_sink_async():
  sink_name:str = f"test_sink_{uuid4()}"
  logging.basicConfig(level=logging.DEBUG)
  pwc:PWC.PW_Control = PWC.PW_Control(monitorOutput="None")

  pwc.delete_all_sinks()
  sinks:dict[str,Any] = pwc.get_sinks()
  assert sink_name not in list(sinks.keys())
  pwc_id:str = pwc.create_null_sink(sink_name, channels=2,duplicates="Exception",waitForExisting=False)
  sinks = pwc.get_sinks()
  found_sinks = False
  for s in sinks.values():
    pass # TODO
  pwc.delete_all_sinks()


def test_delete_sink()->None:
  sink_name:str = f"test_sink_{uuid4()}"
  logging.basicConfig(level=logging.DEBUG)
  pwc:PWC.PW_Control = PWC.PW_Control(monitorOutput="None")

  pwc_name:str = pwc.create_null_sink(sink_name, channels=2,duplicates="Exception",waitForExisting=True)
  sinks:dict[str,Any] = pwc.get_sinks()
  assert pwc_name in list(sinks.keys())
  pwc.delete_null_sink(pwc_name, waitForRemoved=True, handleNotExisting="Exception")
  sinks = pwc.get_sinks()
  assert sink_name not in list(sinks.keys())

def test_delete_all_null_sinks()->None:
  sink_name_1:str = f"test_sink_1_{uuid4()}"
  sink_name_2:str = f"test_sink_2_{uuid4()}"
  logging.basicConfig(level=logging.DEBUG)
  pwc:PWC.PW_Control = PWC.PW_Control(monitorOutput="None")

  sinks:dict[str,Any] = pwc.get_sinks()
  pwc_name_1:str = pwc.create_null_sink(sink_name_1, channels=2,duplicates="Exception",waitForExisting=True)
  pwc_name_2:str = pwc.create_null_sink(sink_name_2, channels=2,duplicates="Exception",waitForExisting=True)
  sinks = pwc.get_sinks()
  sink_names = list(sinks.keys())
  assert pwc_name_1 in sink_names and pwc_name_2 in sink_names
  pwc.delete_all_null_sinks()
  sinks = pwc.get_sinks()
  sink_names = list(sinks.keys())
  assert pwc_name_1 not in sink_names and pwc_name_2 not in sink_names

def test_delete_all_sinks()->None:
  sink_name_1:str = f"test_sink_1_{uuid4()}"
  sink_name_2:str = f"test_sink_2_{uuid4()}"
  logging.basicConfig(level=logging.DEBUG)
  pwc:PWC.PW_Control = PWC.PW_Control(monitorOutput="None")

  pwc_name_1:str = pwc.create_null_sink(sink_name_1, channels=2,duplicates="Exception",waitForExisting=True)
  pwc_name_2:str = pwc.create_null_sink(sink_name_2, channels=2,duplicates="Exception",waitForExisting=True)
  sinks:dict[str,Any] = pwc.get_sinks()
  sink_names:list[str] = list(sinks.keys())
  assert pwc_name_1 in sink_names and pwc_name_2 in sink_names

  pwc.delete_all_sinks()
  sinks = pwc.get_sinks()
  sink_names:list[str] = list(sinks.keys())
  assert pwc_name_1 not in sink_names and pwc_name_2 not in sink_names

def all():

  logging.basicConfig(level=logging.DEBUG)

  pwc = PWC.PW_Control(monitorOutput="None")

  ss = pwc.get_sinks()
  pprint(list(ss.keys()))
  pprint(ss,width=200,indent=1)
  print("_Printed all Sinks_\n")

  pwc.delete_all_null_sinks()

  print("_Deleted all null Sinks_\n")

  msn_1:str = pwc.create_null_sink("my_sink_1", channels=2,duplicates="ignore",waitForExisting=True)
  msn_2:str = pwc.create_null_sink("my_sink_2", channels=2,duplicates="ignore",waitForExisting=True)
  msn_1_b:str = pwc.create_null_sink("my_sink_1", channels=2,duplicates="ignore",waitForExisting=True)
  print(f"_Created Sinks {msn_1} {msn_2} {msn_1_b}_\n")
  ss = pwc.get_sinks()
  pprint(list(ss.keys()))

  pwc.connect(f"{msn_1}:monitor_FL",f"{msn_2}:playback_FL", raiseOnError=True)
  pwc.connect(f"{msn_1}:monitor_FR",f"{msn_2}:playback_FR", raiseOnError=True)

  print("_Connected 1 to 2_\n")

  return
  pwc.disconnect("spotify:output_FL","analog-stereo:playback_FL",raiseOnError=False)
  pwc.disconnect("spotify:output_FR","analog-stereo:playback_FR",raiseOnError=False)
  print("_Disconnected spotify from analog-stereo_\n")

  ss = pwc.get_sinks()
  pprint([ss.keys()])
  pprint(ss)

  pwc.connect("spotify:output_FL","intermed_sink:playback_FL", raiseOnError=False)
  pwc.connect("spotify:output_FR","intermed_sink:playback_FR", raiseOnError=False)
  print("_connected spotify to intermed_sink_\n")

#pwc.connect("intermed_sink:monitor_FL","alsa:pcm:0:front:0:playback:playback_0")
  pwc.connect("intermed_sink:monitor_FR","analog-stereo:playback_FR", raiseOnError=False)
  print("_connected intermed_sink to analog-stere right\n")


if __name__ == "__main__":
  all()


