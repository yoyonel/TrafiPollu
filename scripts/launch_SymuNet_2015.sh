#! /bin/bash

# url: http://arstechnica.com/civis/viewtopic.php?f=16&t=113430

catcher ()
{
	echo "SegFault!"
	run_SymuNet
}

run_SymuNet ()
{
	wine '/home/atty/Prog/New Symunet/SymuNet.exe'		
}

trap catcher ERR

run_SymuNet


