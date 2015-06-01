/*
* Copyright 2014 Open Connectome Project (http://openconnecto.me)
* 
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
* 
*     http://www.apache.org/licenses/LICENSE-2.0
* 
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*/

/*
 * Header File for OCP Ctype Functions
*/
 
#include<stdint.h>

// Declaring Naive implementation for filterCutout
extern "C" void filterCutout ( uint32_t * , int , uint32_t *, int );

// Declaring the OpenMP implementation for filterCutout
extern "C" void filterCutoutOMP ( uint32_t *, int , uint32_t *, int );

// Decalring the OpenMP cache optimized implementation for filterCutout
extern "C" void filterCutoutOMPCache ( uint32_t *, int, uint32_t *, int );

// Declaring the annotateCube implementation
extern "C" int annotateCube ( uint32_t * , int , int * , int , uint32_t * , uint32_t [][3] , int , char, uint32_t [][3] );

// Declaring the locateCube implementation
extern "C" void locateCube ( uint64_t [][4] , int , uint32_t [][3] , int , int * );

// Declaring XYZMorton zindex function
extern "C" uint64_t XYZMorton ( uint64_t * );

// Declaring MortonXYZ zindex function
extern "C" void MortonXYZ ( uint64_t , uint64_t [3] );

// Declaring recolorSlice function
extern "C" void recolorCubeOMP ( uint32_t * , int , int , uint32_t * , uint32_t * ); 

// Declaring Quick Sort function
extern "C" void quicksort ( uint64_t [][4] , int ); 

// Declaring the shaveCube function
extern "C" void shaveCube ( uint32_t * , int , int * , int , uint32_t * , uint32_t [][3] , int , uint32_t [][3] , int , uint32_t [][3] , int );

// Declaring the annotateEntityDense function
extern "C" void annotateEntityDense ( uint32_t * , int * , int );

// Declaring the shaveDense function
extern "C" void shaveDense ( uint32_t * , uint32_t * , int * );

// Declaring the exceptionDense function
extern "C" void exceptionDense ( uint32_t * , uint32_t * , int * );

// Declaring the exceptionDense function
extern "C" void overwriteDense ( uint32_t * , uint32_t * , int * );

// Declaring the zoomOutData function
extern "C" void zoomOutData ( uint32_t * , uint32_t * , int * , int );

// Declaring the zoomOutData function OMP optimized
extern "C" void zoomOutDataOMP ( uint32_t * , uint32_t * , int * , int );

// Declaring the zoomInData function
extern "C" void zoomInData ( uint32_t * , uint32_t * , int * , int );

// Declaring the zoomInData function OMP optimized
extern "C" void zoomInDataOMP ( uint32_t * , uint32_t * , int * , int );

// Declaring the mergeCube function
extern "C" void mergeCube ( uint32_t * , int * , int , int );

// Declaring the isotropicBuild function
extern "C" void isotropicBuild8 ( uint8_t * , uint8_t *, uint8_t *, int * );
extern "C" void isotropicBuild16 ( uint16_t * , uint16_t *, uint16_t *, int * );
extern "C" void isotropicBuild32 ( uint32_t * , uint32_t *, uint32_t *, int * );
