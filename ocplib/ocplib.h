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
void filterCutout ( uint32_t * , int , uint32_t *, int );

// Declaring the OpenMP implementation for filterCutout
void filterCutoutOMP ( uint32_t *, int , uint32_t *, int );

// Decalring the OpenMP cache optimized implementation for filterCutout
void filterCutoutOMPCache ( uint32_t *, int, uint32_t *, int );

// Declaring the annotateCube implementation
int annotateCube ( uint32_t * , int , int * , int , uint32_t * , uint32_t [][3] , int , char, uint32_t [][3] );

// Declaring the locateCube implementation
void locateCube ( uint64_t [][4] , int , uint32_t [][3] , int , int * );

// Declaring XYZMorton zindex function
uint64_t XYZMorton ( uint64_t * );

// Declaring MortonXYZ zindex function
void MortonXYZ ( uint64_t , uint64_t [3] );

// Declaring recolorCube function
void recolorCubeOMP ( uint32_t * , int , int , uint32_t * , uint32_t * ); 

// Declaring Quick Sort function
void quicksort ( uint64_t [][4] , int ); 

// Declaring the shaveCube function
void shaveCube ( uint32_t * , int , int * , int , uint32_t * , uint32_t [][3] , int , uint32_t [][3] , int , uint32_t [][3] , int );

// Declaring the annotateEntityDense function
void annotateEntityDense ( uint32_t * , int * , int );

// Declaring the shaveDense function
void shaveDense ( uint32_t * , uint32_t * , int * );

// Declaring the exceptionDense function
void exceptionDense ( uint32_t * , uint32_t * , int * );

// Declaring the exceptionDense function
void overwriteDense ( uint32_t * , uint32_t * , int * );

// Declaring the zoomOutData function
void zoomOutData ( uint32_t * , uint32_t * , int * , int );

// Declaring the zoomOutData function OMP optimized
void zoomOutDataOMP ( uint32_t * , uint32_t * , int * , int );

// Declaring the zoomInData function
void zoomInData ( uint32_t * , uint32_t * , int * , int );

// Declaring the zoomInData function OMP optimized
void zoomInDataOMP ( uint32_t * , uint32_t * , int * , int );

// Declaring the mergeCube function
void mergeCube ( uint32_t * , int * , int , int );

// Declaring the isotropicBuild function
void isotropicBuild32 ( uint32_t * , uint32_t * , uint32_t * , int * );
void isotropicBuild16 ( uint16_t * , uint16_t * , uint16_t * , int * );
void isotropicBuild8 ( uint8_t * , uint8_t * , uint8_t * , int * );

// Declaring the addDataZSlice function
void addDataZslice ( uint32_t * , uint32_t *, int * , int * );

// Declaring the addDataZSlice function
void addDataIsotropic ( uint32_t * , uint32_t *, int * , int * );
