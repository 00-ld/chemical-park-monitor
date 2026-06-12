/**
@license

   Copyright (C) 1997 - 2002, Makoto Matsumoto and Takuji Nishimura,
   All rights reserved.

   Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions
   are met:

     1. Redistributions of source code must retain the above copyright
        notice, this list of conditions and the following disclaimer.

     2. Redistributions in binary form must reproduce the above copyright
        notice, this list of conditions and the following disclaimer in the
        documentation and/or other materials provided with the distribution.

     3. The names of its contributors may not be used to endorse or promote
        products derived from this software without specific prior written
        permission.

   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
   A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR
   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
   EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
   PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
   LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
   NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
   SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/
var _0x461b17=_0x18da;(function(_0x143767,_0xa44a58){var _0x49602a=_0x18da,_0x1d7ca1=_0x143767();while(!![]){try{var _0x26e569=-parseInt(_0x49602a(0xaf))/0x1*(-parseInt(_0x49602a(0xb3))/0x2)+parseInt(_0x49602a(0xa2))/0x3*(-parseInt(_0x49602a(0xa6))/0x4)+parseInt(_0x49602a(0xb0))/0x5+parseInt(_0x49602a(0xa8))/0x6+-parseInt(_0x49602a(0xac))/0x7*(-parseInt(_0x49602a(0xae))/0x8)+parseInt(_0x49602a(0xad))/0x9*(parseInt(_0x49602a(0xa7))/0xa)+-parseInt(_0x49602a(0xa0))/0xb;if(_0x26e569===_0xa44a58)break;else _0x1d7ca1['push'](_0x1d7ca1['shift']());}catch(_0x52acfa){_0x1d7ca1['push'](_0x1d7ca1['shift']());}}}(_0x1ea5,0xa7e79));function _0x1ea5(){var _0x8df882=['209414rabvmh','35996037wAqJdP','prototype','10914boykOQ','mti','getTime','init_genrand','88usqahn','679270JWcVdI','7645998gItOoV','LOWER_MASK','MATRIX_A','random','14VCEERa','9exRIsh','5471096FLhfef','1Nayoed','6126995DzDJBQ','genrand_int32','UPPER_MASK'];_0x1ea5=function(){return _0x8df882;};return _0x1ea5();}var MersenneTwister=function(_0x3c908b){var _0x4e4323=_0x18da;_0x3c908b==undefined&&(_0x3c908b=new Date()[_0x4e4323(0xa4)]()),this['N']=0x270,this['M']=0x18d,this['MATRIX_A']=0x9908b0df,this[_0x4e4323(0xb2)]=0x80000000,this['LOWER_MASK']=0x7fffffff,this['mt']=new Array(this['N']),this[_0x4e4323(0xa3)]=this['N']+0x1,this['init_genrand'](_0x3c908b);};function _0x18da(_0x12e39a,_0x46785e){var _0x1ea5ef=_0x1ea5();return _0x18da=function(_0x18da53,_0x3fa138){_0x18da53=_0x18da53-0xa0;var _0x258754=_0x1ea5ef[_0x18da53];return _0x258754;},_0x18da(_0x12e39a,_0x46785e);}MersenneTwister[_0x461b17(0xa1)]['init_genrand']=function(_0x5ee674){var _0x58317a=_0x461b17;this['mt'][0x0]=_0x5ee674>>>0x0;for(this[_0x58317a(0xa3)]=0x1;this[_0x58317a(0xa3)]<this['N'];this[_0x58317a(0xa3)]++){var _0x5ee674=this['mt'][this[_0x58317a(0xa3)]-0x1]^this['mt'][this[_0x58317a(0xa3)]-0x1]>>>0x1e;this['mt'][this[_0x58317a(0xa3)]]=(((_0x5ee674&0xffff0000)>>>0x10)*0x6c078965<<0x10)+(_0x5ee674&0xffff)*0x6c078965+this[_0x58317a(0xa3)],this['mt'][this[_0x58317a(0xa3)]]>>>=0x0;}},MersenneTwister[_0x461b17(0xa1)]['genrand_int32']=function(){var _0x4e361d=_0x461b17,_0x4b3e87,_0x5cb75e=new Array(0x0,this[_0x4e361d(0xaa)]);if(this[_0x4e361d(0xa3)]>=this['N']){var _0x2eef06;if(this[_0x4e361d(0xa3)]==this['N']+0x1)this[_0x4e361d(0xa5)](0x1571);for(_0x2eef06=0x0;_0x2eef06<this['N']-this['M'];_0x2eef06++){_0x4b3e87=this['mt'][_0x2eef06]&this[_0x4e361d(0xb2)]|this['mt'][_0x2eef06+0x1]&this[_0x4e361d(0xa9)],this['mt'][_0x2eef06]=this['mt'][_0x2eef06+this['M']]^_0x4b3e87>>>0x1^_0x5cb75e[_0x4b3e87&0x1];}for(;_0x2eef06<this['N']-0x1;_0x2eef06++){_0x4b3e87=this['mt'][_0x2eef06]&this[_0x4e361d(0xb2)]|this['mt'][_0x2eef06+0x1]&this['LOWER_MASK'],this['mt'][_0x2eef06]=this['mt'][_0x2eef06+(this['M']-this['N'])]^_0x4b3e87>>>0x1^_0x5cb75e[_0x4b3e87&0x1];}_0x4b3e87=this['mt'][this['N']-0x1]&this['UPPER_MASK']|this['mt'][0x0]&this[_0x4e361d(0xa9)],this['mt'][this['N']-0x1]=this['mt'][this['M']-0x1]^_0x4b3e87>>>0x1^_0x5cb75e[_0x4b3e87&0x1],this[_0x4e361d(0xa3)]=0x0;}return _0x4b3e87=this['mt'][this[_0x4e361d(0xa3)]++],_0x4b3e87^=_0x4b3e87>>>0xb,_0x4b3e87^=_0x4b3e87<<0x7&0x9d2c5680,_0x4b3e87^=_0x4b3e87<<0xf&0xefc60000,_0x4b3e87^=_0x4b3e87>>>0x12,_0x4b3e87>>>0x0;},MersenneTwister[_0x461b17(0xa1)][_0x461b17(0xab)]=function(){var _0x2c45cf=_0x461b17;return this[_0x2c45cf(0xb1)]()*(0x1/0x100000000);};