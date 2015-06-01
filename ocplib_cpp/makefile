#m.PHONY : clean

# Make file for Unix Systems

all: clean ocplib.so

ocplib.so : filterCutout.o filterCutoutOMP.o locateCube.o annotateCube.o shaveCube.o mergeCube.o annotateEntityDense.o shaveDense.o exceptionDense.o overwriteDense.o zindex.o recolorCube.o zoomData.o quicksort.o isotropicBuild.o
	g++ -shared -fopenmp -O3 -o ocplib.so filterCutout.o filterCutoutOMP.o locateCube.o annotateCube.o shaveCube.o mergeCube.o annotateEntityDense.o shaveDense.o exceptionDense.o overwriteDense.o zindex.o recolorCube.o zoomData.o quicksort.o isotropicBuild.o -I .

filterCutout.o : filterCutout.cpp
	g++ -c -fPIC -O3 filterCutout.cpp -o filterCutout.o -I .

filterCutoutOMP.o : filterCutoutOMP.cpp
	 g++ -c -fopenmp -fPIC -O3 filterCutoutOMP.cpp -o filterCutoutOMP.o -I .

locateCube.o : locateCube.cpp
	g++ -c -fPIC -O3 locateCube.cpp -o locateCube.o -I .

annotateCube.o : annotateCube.cpp
	g++ -c -fPIC -O3 annotateCube.cpp -o annotateCube.o -I .

shaveCube.o : shaveCube.cpp
	g++ -c -fPIC -O3 shaveCube.cpp -o shaveCube.o -I .

mergeCube.o : mergeCube.cpp
	g++ -c -fPIC -O3 mergeCube.cpp -o mergeCube.o -I .

annotateEntityDense.o : annotateEntityDense.cpp
	g++ -c -fPIC -O3 annotateEntityDense.cpp -o annotateEntityDense.o -I .

shaveDense.o : shaveDense.cpp
	g++ -c -fPIC -O3 shaveDense.cpp -o shaveDense.o -I .

exceptionDense.o : exceptionDense.cpp
	g++ -c -fPIC -O3 exceptionDense.cpp -o exceptionDense.o -I .

overwriteDense.o : overwriteDense.cpp
	g++ -c -fPIC -O3 overwriteDense.cpp -o overwriteDense.o -I .

zindex.o : zindex.cpp
	g++ -c -fPIC -O3 zindex.cpp -o zindex.o -I .

recolorCube.o : recolorCube.cpp
	g++ -c -fopenmp -fPIC -O3 recolorCube.cpp -o recolorCube.o -I .

zoomData.o : zoomData.cpp
	g++ -c -fopenmp -fPIC -O3 zoomData.cpp -o zoomData.o -I .

quicksort.o : quicksort.cpp
	g++ -c -fPIC -O3 quicksort.cpp -o quicksort.o -I .

isotropicBuild.o : isotropicBuild.cpp
	g++ -c -fPIC -O3 isotropicBuild.cpp -o isotropicBuild.o -I .

test : clean testmain.c
	g++ -ggdb testmain.c quicksort.c -o test -I .

clean :
	-rm -vf ocplib.so zindex.o locateCube.o annotateCube.o shaveCube.o mergeCube.o annotateEntityDense.o shaveDense.o exceptionDense.o overwriteDense.o filterCutout.o filterCutoutOMP.o recolorCube.o zoomData.o quicksort.o isotropicBuild.o test
