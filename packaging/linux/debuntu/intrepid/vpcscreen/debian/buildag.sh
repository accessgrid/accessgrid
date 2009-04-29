

echo "YYY ${topdir}"
echo "ZZZ ${version}"

( cd common && scons configure && scons )
echo "DONE COMMON"
( cd VPMedia && scons TOP_DIR=${topdir} configure && scons TOP_DIR=${topdir} )
echo "DONE VPMEDIA"
( cd VPC && scons TOP_DIR=${topdir} )
echo "DONE VPC"
( cd VPCScreen-${version} && scons TOP_DIR=${topdir}
zip -0 VPCScreenProducerService.zip VPCScreenProducerService.py VPCScreenProducerService.svc
)
echo "DONE VPCSCREEN"

