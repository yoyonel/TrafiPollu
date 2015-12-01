#! /bin/bash

# url: http://arstechnica.com/civis/viewtopic.php?f=16&t=113430

catcher ()
{
	echo "SegFault!"
	run_SymuNet
}

run_SymuNet ()
{
	echo "Running: $SYMUNET_BINDIR/SymuNet.exe ..."
	wine $SYMUNET_BINDIR/SymuNet.exe
}

path_to_symunet=$SYMUNET_BINDIR/SymuNet.exe
# url: http://tldp.org/LDP/Bash-Beginners-Guide/html/sect_07_01.html
if [ -a $path_to_symunet ]; then
    trap catcher ERR
    run_SymuNet
else
    echo "ERROR"
    echo "Probleme pour trouver SymuNet.exe à l'emplacement décrit par la variable d'envirronement SYMUNET_BINDIR=$SYMUNET_BINDIR"
    echo
    echo "  (Redéfinissez la variable d'env. SYMUNET_BINDIR dans set_env_for_SymuNet.sh"
    echo "   >> Pistes de recherches:"
    # url: http://stackoverflow.com/a/15184414
    echo "   $(locate 'SymuNet.exe')"
    echo "  )"
fi