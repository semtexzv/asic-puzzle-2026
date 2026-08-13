`timescale 1ns/1ps
`define UNIT_DELAY
`define FUNCTIONAL
`default_nettype none
/*
 * Copyright 2020 The SkyWater PDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
*/


`ifndef SKY130_FD_SC_HD__A21BO_FUNCTIONAL_V
`define SKY130_FD_SC_HD__A21BO_FUNCTIONAL_V

/**
 * a21bo: 2-input AND into first input of 2-input OR,
 *        2nd input inverted.
 *
 *        X = ((A1 & A2) | (!B1_N))
 *
 * Verilog simulation functional model.
 */

`timescale 1ns / 1ps
`default_nettype none

`celldefine
module sky130_fd_sc_hd__a21bo (
    X   ,
    A1  ,
    A2  ,
    B1_N
);

    // Module ports
    output X   ;
    input  A1  ;
    input  A2  ;
    input  B1_N;

    // Local signals
    wire nand0_out  ;
    wire nand1_out_X;

    //   Name   Output       Other arguments
    nand nand0 (nand0_out  , A2, A1         );
    nand nand1 (nand1_out_X, B1_N, nand0_out);
    buf  buf0  (X          , nand1_out_X    );

endmodule
`endcelldefine

`default_nettype wire
`endif  // SKY130_FD_SC_HD__A21BO_FUNCTIONAL_V
/*
 * Copyright 2020 The SkyWater PDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
*/


`ifndef SKY130_FD_SC_HD__A21BOI_FUNCTIONAL_V
`define SKY130_FD_SC_HD__A21BOI_FUNCTIONAL_V

/**
 * a21boi: 2-input AND into first input of 2-input NOR,
 *         2nd input inverted.
 *
 *         Y = !((A1 & A2) | (!B1_N))
 *
 * Verilog simulation functional model.
 */

`timescale 1ns / 1ps
`default_nettype none

`celldefine
module sky130_fd_sc_hd__a21boi (
    Y   ,
    A1  ,
    A2  ,
    B1_N
);

    // Module ports
    output Y   ;
    input  A1  ;
    input  A2  ;
    input  B1_N;

    // Local signals
    wire b         ;
    wire and0_out  ;
    wire nor0_out_Y;

    //  Name  Output      Other arguments
    not not0 (b         , B1_N           );
    and and0 (and0_out  , A1, A2         );
    nor nor0 (nor0_out_Y, b, and0_out    );
    buf buf0 (Y         , nor0_out_Y     );

endmodule
`endcelldefine

`default_nettype wire
`endif  // SKY130_FD_SC_HD__A21BOI_FUNCTIONAL_V
/*
 * Copyright 2020 The SkyWater PDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
*/


`ifndef SKY130_FD_SC_HD__A21O_FUNCTIONAL_V
`define SKY130_FD_SC_HD__A21O_FUNCTIONAL_V

/**
 * a21o: 2-input AND into first input of 2-input OR.
 *
 *       X = ((A1 & A2) | B1)
 *
 * Verilog simulation functional model.
 */

`timescale 1ns / 1ps
`default_nettype none

`celldefine
module sky130_fd_sc_hd__a21o (
    X ,
    A1,
    A2,
    B1
);

    // Module ports
    output X ;
    input  A1;
    input  A2;
    input  B1;

    // Local signals
    wire and0_out ;
    wire or0_out_X;

    //  Name  Output     Other arguments
    and and0 (and0_out , A1, A2         );
    or  or0  (or0_out_X, and0_out, B1   );
    buf buf0 (X        , or0_out_X      );

endmodule
`endcelldefine

`default_nettype wire
`endif  // SKY130_FD_SC_HD__A21O_FUNCTIONAL_V
/*
 * Copyright 2020 The SkyWater PDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
*/


`ifndef SKY130_FD_SC_HD__A31O_FUNCTIONAL_V
`define SKY130_FD_SC_HD__A31O_FUNCTIONAL_V

/**
 * a31o: 3-input AND into first input of 2-input OR.
 *
 *       X = ((A1 & A2 & A3) | B1)
 *
 * Verilog simulation functional model.
 */

`timescale 1ns / 1ps
`default_nettype none

`celldefine
module sky130_fd_sc_hd__a31o (
    X ,
    A1,
    A2,
    A3,
    B1
);

    // Module ports
    output X ;
    input  A1;
    input  A2;
    input  A3;
    input  B1;

    // Local signals
    wire and0_out ;
    wire or0_out_X;

    //  Name  Output     Other arguments
    and and0 (and0_out , A3, A1, A2     );
    or  or0  (or0_out_X, and0_out, B1   );
    buf buf0 (X        , or0_out_X      );

endmodule
`endcelldefine

`default_nettype wire
`endif  // SKY130_FD_SC_HD__A31O_FUNCTIONAL_V
/*
 * Copyright 2020 The SkyWater PDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
*/


`ifndef SKY130_FD_SC_HD__AND2_FUNCTIONAL_V
`define SKY130_FD_SC_HD__AND2_FUNCTIONAL_V

/**
 * and2: 2-input AND.
 *
 * Verilog simulation functional model.
 */

`timescale 1ns / 1ps
`default_nettype none

`celldefine
module sky130_fd_sc_hd__and2 (
    X,
    A,
    B
);

    // Module ports
    output X;
    input  A;
    input  B;

    // Local signals
    wire and0_out_X;

    //  Name  Output      Other arguments
    and and0 (and0_out_X, A, B           );
    buf buf0 (X         , and0_out_X     );

endmodule
`endcelldefine

`default_nettype wire
`endif  // SKY130_FD_SC_HD__AND2_FUNCTIONAL_V
/*
 * Copyright 2020 The SkyWater PDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
*/


`ifndef SKY130_FD_SC_HD__AND3_FUNCTIONAL_V
`define SKY130_FD_SC_HD__AND3_FUNCTIONAL_V

/**
 * and3: 3-input AND.
 *
 * Verilog simulation functional model.
 */

`timescale 1ns / 1ps
`default_nettype none

`celldefine
module sky130_fd_sc_hd__and3 (
    X,
    A,
    B,
    C
);

    // Module ports
    output X;
    input  A;
    input  B;
    input  C;

    // Local signals
    wire and0_out_X;

    //  Name  Output      Other arguments
    and and0 (and0_out_X, C, A, B        );
    buf buf0 (X         , and0_out_X     );

endmodule
`endcelldefine

`default_nettype wire
`endif  // SKY130_FD_SC_HD__AND3_FUNCTIONAL_V
/*
 * Copyright 2020 The SkyWater PDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
*/


`ifndef SKY130_FD_SC_HD__AND4BB_FUNCTIONAL_V
`define SKY130_FD_SC_HD__AND4BB_FUNCTIONAL_V

/**
 * and4bb: 4-input AND, first two inputs inverted.
 *
 * Verilog simulation functional model.
 */

`timescale 1ns / 1ps
`default_nettype none

`celldefine
module sky130_fd_sc_hd__and4bb (
    X  ,
    A_N,
    B_N,
    C  ,
    D
);

    // Module ports
    output X  ;
    input  A_N;
    input  B_N;
    input  C  ;
    input  D  ;

    // Local signals
    wire nor0_out  ;
    wire and0_out_X;

    //  Name  Output      Other arguments
    nor nor0 (nor0_out  , A_N, B_N       );
    and and0 (and0_out_X, nor0_out, C, D );
    buf buf0 (X         , and0_out_X     );

endmodule
`endcelldefine

`default_nettype wire
`endif  // SKY130_FD_SC_HD__AND4BB_FUNCTIONAL_V
/*
 * Copyright 2020 The SkyWater PDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
*/


`ifndef SKY130_FD_SC_HD__CLKBUF_FUNCTIONAL_V
`define SKY130_FD_SC_HD__CLKBUF_FUNCTIONAL_V

/**
 * clkbuf: Clock tree buffer.
 *
 * Verilog simulation functional model.
 */

`timescale 1ns / 1ps
`default_nettype none

`celldefine
module sky130_fd_sc_hd__clkbuf (
    X,
    A
);

    // Module ports
    output X;
    input  A;

    // Local signals
    wire buf0_out_X;

    //  Name  Output      Other arguments
    buf buf0 (buf0_out_X, A              );
    buf buf1 (X         , buf0_out_X     );

endmodule
`endcelldefine

`default_nettype wire
`endif  // SKY130_FD_SC_HD__CLKBUF_FUNCTIONAL_V
/*
 * Copyright 2020 The SkyWater PDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
*/


`ifndef SKY130_FD_SC_HD__DFRTP_FUNCTIONAL_V
`define SKY130_FD_SC_HD__DFRTP_FUNCTIONAL_V

/**
 * dfrtp: Delay flop, inverted reset, single output.
 *
 * Verilog simulation functional model.
 */

`timescale 1ns / 1ps
`default_nettype none

// Import user defined primitives.
`include "/Users/semtexzv/asic-puzzle-2026/lib/sky130_fd_sc_hd/models/udp_dff_pr/sky130_fd_sc_hd__udp_dff_pr.v"

`celldefine
module sky130_fd_sc_hd__dfrtp (
    Q      ,
    CLK    ,
    D      ,
    RESET_B
);

    // Module ports
    output Q      ;
    input  CLK    ;
    input  D      ;
    input  RESET_B;

    // Local signals
    wire buf_Q;
    wire RESET;

    //                          Delay       Name  Output  Other arguments
    not                                     not0 (RESET , RESET_B        );
    sky130_fd_sc_hd__udp_dff$PR `UNIT_DELAY dff0 (buf_Q , D, CLK, RESET  );
    buf                                     buf0 (Q     , buf_Q          );

endmodule
`endcelldefine

`default_nettype wire
`endif  // SKY130_FD_SC_HD__DFRTP_FUNCTIONAL_V
/*
 * Copyright 2020 The SkyWater PDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
*/


`ifndef SKY130_FD_SC_HD__MUX2_FUNCTIONAL_V
`define SKY130_FD_SC_HD__MUX2_FUNCTIONAL_V

/**
 * mux2: 2-input multiplexer.
 *
 * Verilog simulation functional model.
 */

`timescale 1ns / 1ps
`default_nettype none

// Import user defined primitives.
`include "/Users/semtexzv/asic-puzzle-2026/lib/sky130_fd_sc_hd/models/udp_mux_2to1/sky130_fd_sc_hd__udp_mux_2to1.v"

`celldefine
module sky130_fd_sc_hd__mux2 (
    X ,
    A0,
    A1,
    S
);

    // Module ports
    output X ;
    input  A0;
    input  A1;
    input  S ;

    // Local signals
    wire mux_2to10_out_X;

    //                            Name       Output           Other arguments
    sky130_fd_sc_hd__udp_mux_2to1 mux_2to10 (mux_2to10_out_X, A0, A1, S      );
    buf                           buf0      (X              , mux_2to10_out_X);

endmodule
`endcelldefine

`default_nettype wire
`endif  // SKY130_FD_SC_HD__MUX2_FUNCTIONAL_V
/*
 * Copyright 2020 The SkyWater PDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
*/


`ifndef SKY130_FD_SC_HD__NAND2_FUNCTIONAL_V
`define SKY130_FD_SC_HD__NAND2_FUNCTIONAL_V

/**
 * nand2: 2-input NAND.
 *
 * Verilog simulation functional model.
 */

`timescale 1ns / 1ps
`default_nettype none

`celldefine
module sky130_fd_sc_hd__nand2 (
    Y,
    A,
    B
);

    // Module ports
    output Y;
    input  A;
    input  B;

    // Local signals
    wire nand0_out_Y;

    //   Name   Output       Other arguments
    nand nand0 (nand0_out_Y, B, A           );
    buf  buf0  (Y          , nand0_out_Y    );

endmodule
`endcelldefine

`default_nettype wire
`endif  // SKY130_FD_SC_HD__NAND2_FUNCTIONAL_V
/*
 * Copyright 2020 The SkyWater PDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
*/


`ifndef SKY130_FD_SC_HD__NOR2_FUNCTIONAL_V
`define SKY130_FD_SC_HD__NOR2_FUNCTIONAL_V

/**
 * nor2: 2-input NOR.
 *
 * Verilog simulation functional model.
 */

`timescale 1ns / 1ps
`default_nettype none

`celldefine
module sky130_fd_sc_hd__nor2 (
    Y,
    A,
    B
);

    // Module ports
    output Y;
    input  A;
    input  B;

    // Local signals
    wire nor0_out_Y;

    //  Name  Output      Other arguments
    nor nor0 (nor0_out_Y, A, B           );
    buf buf0 (Y         , nor0_out_Y     );

endmodule
`endcelldefine

`default_nettype wire
`endif  // SKY130_FD_SC_HD__NOR2_FUNCTIONAL_V
/*
 * Copyright 2020 The SkyWater PDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
*/


`ifndef SKY130_FD_SC_HD__O21BAI_FUNCTIONAL_V
`define SKY130_FD_SC_HD__O21BAI_FUNCTIONAL_V

/**
 * o21bai: 2-input OR into first input of 2-input NAND, 2nd iput
 *         inverted.
 *
 *         Y = !((A1 | A2) & !B1_N)
 *
 * Verilog simulation functional model.
 */

`timescale 1ns / 1ps
`default_nettype none

`celldefine
module sky130_fd_sc_hd__o21bai (
    Y   ,
    A1  ,
    A2  ,
    B1_N
);

    // Module ports
    output Y   ;
    input  A1  ;
    input  A2  ;
    input  B1_N;

    // Local signals
    wire b          ;
    wire or0_out    ;
    wire nand0_out_Y;

    //   Name   Output       Other arguments
    not  not0  (b          , B1_N           );
    or   or0   (or0_out    , A2, A1         );
    nand nand0 (nand0_out_Y, b, or0_out     );
    buf  buf0  (Y          , nand0_out_Y    );

endmodule
`endcelldefine

`default_nettype wire
`endif  // SKY130_FD_SC_HD__O21BAI_FUNCTIONAL_V
/*
 * Copyright 2020 The SkyWater PDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
*/


`ifndef SKY130_FD_SC_HD__OR2_FUNCTIONAL_V
`define SKY130_FD_SC_HD__OR2_FUNCTIONAL_V

/**
 * or2: 2-input OR.
 *
 * Verilog simulation functional model.
 */

`timescale 1ns / 1ps
`default_nettype none

`celldefine
module sky130_fd_sc_hd__or2 (
    X,
    A,
    B
);

    // Module ports
    output X;
    input  A;
    input  B;

    // Local signals
    wire or0_out_X;

    //  Name  Output     Other arguments
    or  or0  (or0_out_X, B, A           );
    buf buf0 (X        , or0_out_X      );

endmodule
`endcelldefine

`default_nettype wire
`endif  // SKY130_FD_SC_HD__OR2_FUNCTIONAL_V
/*
 * Copyright 2020 The SkyWater PDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
*/


`ifndef SKY130_FD_SC_HD__XNOR2_FUNCTIONAL_V
`define SKY130_FD_SC_HD__XNOR2_FUNCTIONAL_V

/**
 * xnor2: 2-input exclusive NOR.
 *
 *        Y = !(A ^ B)
 *
 * Verilog simulation functional model.
 */

`timescale 1ns / 1ps
`default_nettype none

`celldefine
module sky130_fd_sc_hd__xnor2 (
    Y,
    A,
    B
);

    // Module ports
    output Y;
    input  A;
    input  B;

    // Local signals
    wire xnor0_out_Y;

    //   Name   Output       Other arguments
    xnor xnor0 (xnor0_out_Y, A, B           );
    buf  buf0  (Y          , xnor0_out_Y    );

endmodule
`endcelldefine

`default_nettype wire
`endif  // SKY130_FD_SC_HD__XNOR2_FUNCTIONAL_V
/*
 * Copyright 2020 The SkyWater PDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
*/


`ifndef SKY130_FD_SC_HD__XOR2_FUNCTIONAL_V
`define SKY130_FD_SC_HD__XOR2_FUNCTIONAL_V

/**
 * xor2: 2-input exclusive OR.
 *
 *       X = A ^ B
 *
 * Verilog simulation functional model.
 */

`timescale 1ns / 1ps
`default_nettype none

`celldefine
module sky130_fd_sc_hd__xor2 (
    X,
    A,
    B
);

    // Module ports
    output X;
    input  A;
    input  B;

    // Local signals
    wire xor0_out_X;

    //  Name  Output      Other arguments
    xor xor0 (xor0_out_X, B, A           );
    buf buf0 (X         , xor0_out_X     );

endmodule
`endcelldefine

`default_nettype wire
`endif  // SKY130_FD_SC_HD__XOR2_FUNCTIONAL_V