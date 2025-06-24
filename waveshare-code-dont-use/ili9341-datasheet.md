ILI9341
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color
Specification
Version: V1.05
Document No.: ILI9341_DS_V1.05.pdf
ILI TECHNOLOGY CORP.
8F, No. 38, Taiyuan St., Jhubei City,
Hsinchu Country 302 Taiwan R.O.C.
Tel.886-3-5600099; Fax.886-3-5670585
http://www.ilitek.com
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 2 of 239
Table of Contents
Section Page

1. Introduction.................................................................................................................................................... 7
2. Features ........................................................................................................................................................ 7
3. Block Diagram............................................................................................................................................... 9
4. Pin Descriptions .......................................................................................................................................... 10
5. Pad Arrangement and Coordination............................................................................................................ 15
6. Block Function Description.......................................................................................................................... 24
7. Function Description ................................................................................................................................... 26
   7.1. MCU interfaces .............................................................................................................................. 26
   7.1.1. MCU interface selection ...................................................................................................... 26
   7.1.2. 8080-Ⅰ Series Parallel Interface........................................................................................ 27
   7.1.3. Write Cycle Sequence ......................................................................................................... 28
   7.1.4. Read Cycle Sequence......................................................................................................... 29
   7.1.5. 8080-Ⅱ Series Parallel Interface........................................................................................ 30
   7.1.6. Write Cycle Sequence ......................................................................................................... 31
   7.1.7. Read Cycle Sequence......................................................................................................... 32
   7.1.8. Serial Interface .................................................................................................................... 33
   7.1.9. Write Cycle Sequence ......................................................................................................... 33
   7.1.10. Read Cycle Sequence......................................................................................................... 36
   7.1.11. Data Transfer Break and Recovery ..................................................................................... 40
   7.1.12. Data Transfer Pause............................................................................................................ 42
   7.1.13. Serial Interface Pause (3_wire) ........................................................................................... 43
   7.1.14. Parallel Interface Pause ...................................................................................................... 43
   7.1.15. Data Transfer Mode............................................................................................................. 44
   7.1.16. Data Transfer Method 1....................................................................................................... 44
   7.1.17. Data Transfer Method 2....................................................................................................... 44
   7.2. RGB Interface ................................................................................................................................ 45
   7.2.1. RGB Interface Selection...................................................................................................... 45
   7.2.2. RGB Interface Timing .......................................................................................................... 49
   7.3. VSYNC Interface............................................................................................................................ 52
   7.4. Color Depth Conversion Look Up Table......................................................................................... 55
   7.5. Display Data RAM (DDRAM) ......................................................................................................... 59
   7.6. Display Data Format ...................................................................................................................... 60
   7.6.1. 3-line Serial Interface........................................................................................................... 60
   7.6.2. 4-line Serial Interface........................................................................................................... 63
   7.6.3. 8-bit Parallel MCU Interface ................................................................................................ 65
   7.6.4. 9-bit Parallel MCU Interface ................................................................................................ 67
   7.6.5. 16-bit Parallel MCU Interface .............................................................................................. 70
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 3 of 239
   7.6.6. 18-bit Parallel MCU Interface .............................................................................................. 76
   7.6.7. 6-bit Parallel RGB Interface................................................................................................. 80
   7.6.8. 16-bit Parallel RGB Interface............................................................................................... 82
   7.6.9. 18-bit Parallel RGB Interface............................................................................................... 82
8. Command.................................................................................................................................................... 83
   8.1. Command List ................................................................................................................................ 83
   8.2. Description of Level 1 Command................................................................................................... 89
   8.2.1. NOP (00h)............................................................................................................................ 89
   8.2.2. Software Reset (01h)........................................................................................................... 90
   8.2.3. Read display identification information (04h) ...................................................................... 91
   8.2.4. Read Display Status (09h)................................................................................................... 92
   8.2.5. Read Display Power Mode (0Ah) ........................................................................................ 94
   8.2.6. Read Display MADCTL (0Bh).............................................................................................. 95
   8.2.7. Read Display Pixel Format (0Ch)........................................................................................ 96
   8.2.8. Read Display Image Format (0Dh)...................................................................................... 97
   8.2.9. Read Display Signal Mode (0Eh) ........................................................................................ 98
   8.2.10. Read Display Self-Diagnostic Result (0Fh)......................................................................... 99
   8.2.11. Enter Sleep Mode (10h) .................................................................................................... 100
   8.2.12. Sleep Out (11h).................................................................................................................. 101
   8.2.13. Partial Mode ON (12h)....................................................................................................... 103
   8.2.14. Normal Display Mode ON (13h) ........................................................................................ 104
   8.2.15. Display Inversion OFF (20h).............................................................................................. 105
   8.2.16. Display Inversion ON (21h) ............................................................................................... 106
   8.2.17. Gamma Set (26h) .............................................................................................................. 107
   8.2.18. Display OFF (28h) ............................................................................................................. 108
   8.2.19. Display ON (29h) ............................................................................................................... 109
   8.2.20. Column Address Set (2Ah)................................................................................................ 110
   8.2.21. Page Address Set (2Bh).................................................................................................... 112
   8.2.22. Memory Write (2Ch) .......................................................................................................... 114
   8.2.23. Color Set (2Dh).................................................................................................................. 115
   8.2.24. Memory Read (2Eh) .......................................................................................................... 116
   8.2.25. Partial Area (30h)............................................................................................................... 118
   8.2.26. Vertical Scrolling Definition (33h) ...................................................................................... 120
   8.2.27. Tearing Effect Line OFF (34h) ........................................................................................... 124
   8.2.28. Tearing Effect Line ON (35h)............................................................................................. 125
   8.2.29. Memory Access Control (36h) ........................................................................................... 127
   8.2.30. Vertical Scrolling Start Address (37h) ................................................................................ 129
   8.2.31. Idle Mode OFF (38h) ......................................................................................................... 131
   8.2.32. Idle Mode ON (39h) ........................................................................................................... 132
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 4 of 239
   8.2.33. COLMOD: Pixel Format Set (3Ah) .................................................................................... 134
   8.2.34. Write_Memory_Continue (3Ch)......................................................................................... 135
   8.2.35. Read_Memory_Continue (3Eh)......................................................................................... 137
   8.2.36. Set_Tear_Scanline (44h)................................................................................................... 139
   8.2.37. Get_Scanline (45h)............................................................................................................ 140
   8.2.38. Write Display Brightness (51h).......................................................................................... 141
   8.2.39. Read Display Brightness (52h).......................................................................................... 142
   8.2.40. Write CTRL Display (53h).................................................................................................. 143
   8.2.41. Read CTRL Display (54h) ................................................................................................. 145
   8.2.42. Write Content Adaptive Brightness Control (55h).............................................................. 147
   8.2.43. Read Content Adaptive Brightness Control (56h) ............................................................. 148
   8.2.44. Write CABC Minimum Brightness (5Eh)............................................................................ 149
   8.2.45. Read CABC Minimum Brightness (5Fh)............................................................................ 150
   8.2.46. Read ID1 (DAh) ................................................................................................................. 151
   8.2.47. Read ID2 (DBh) ................................................................................................................. 152
   8.2.48. Read ID3 (DCh)................................................................................................................. 153
   8.3. Description of Level 2 Command................................................................................................. 154
   8.3.1. RGB Interface Signal Control (B0h) .................................................................................. 154
   8.3.2. Frame Rate Control (In Normal Mode/Full Colors) (B1h).................................................. 155
   8.3.3. Frame Rate Control (In Idle Mode/8 colors) (B2h) ............................................................ 157
   8.3.4. Frame Rate control (In Partial Mode/Full Colors) (B3h).................................................... 159
   8.3.5. Display Inversion Control (B4h)......................................................................................... 161
   8.3.6. Blanking Porch Control (B5h)............................................................................................ 162
   8.3.7. Display Function Control (B6h).......................................................................................... 164
   8.3.8. Entry Mode Set (B7h)........................................................................................................ 168
   8.3.9. Backlight Control 1 (B8h)................................................................................................... 169
   8.3.10. Backlight Control 2 (B9h)................................................................................................... 170
   8.3.11. Backlight Control 3 (BAh) .................................................................................................. 172
   8.3.12. Backlight Control 4 (BBh) .................................................................................................. 173
   8.3.13. Backlight Control 5 (BCh).................................................................................................. 175
   8.3.14. Backlight Control 7 (BEh) .................................................................................................. 176
   8.3.15. Backlight Control 8 (BFh) .................................................................................................. 177
   8.3.16. Power Control 1 (C0h)....................................................................................................... 178
   8.3.17. Power Control 2 (C1h)....................................................................................................... 179
   8.3.18. VCOM Control 1(C5h) ....................................................................................................... 180
   8.3.19. VCOM Control 2(C7h) ....................................................................................................... 182
   8.3.20. NV Memory Write (D0h) .................................................................................................... 184
   8.3.21. NV Memory Protection Key (D1h) ..................................................................................... 185
   8.3.22. NV Memory Status Read (D2h)......................................................................................... 186
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 5 of 239
   8.3.23. Read ID4 (D3h) ................................................................................................................. 187
   8.3.24. Positive Gamma Correction (E0h)..................................................................................... 188
   8.3.25. Negative Gamma Correction (E1h) ................................................................................... 189
   8.3.26. Digital Gamma Control 1 (E2h) ......................................................................................... 190
   8.3.27. Digital Gamma Control 2(E3h) .......................................................................................... 191
   8.3.28. Interface Control (F6h) ...................................................................................................... 192
   8.4 Description of extend register command……………………………………………………………….195
   8.4.1. Power control A (CBh)…………………………………………………………………………..195
   8.4.2. Power control B (CFh)…………………………………………………………………………..196
   8.4.3. Driver timing control A (E8h)……………………………………….…………………………...197
   8.4.4. Driver timing control B (EAh)…………...............................................................................198
   8.4.5. Power on sequence control (EDh)……………………………………………………………..199
   8.4.6. Enable 3 gamma (F2h)…………………………………………………………………………..200
   8.4.7. Pump ratio control (F7h)………………………………………………………………………...201
9. Display Data RAM..................................................................................................................................... 202
   9.1. Configuration................................................................................................................................ 202
   9.2. Memory to Display Address Mapping .......................................................................................... 203
   9.2.1. Normal Display ON or Partial Mode ON, Vertical Scroll Mode OFF.................................. 203
   9.2.2. Vertical Scroll Mode........................................................................................................... 204
   9.2.3. Vertical Scroll Example...................................................................................................... 205
   9.2.4. Case1: TFA+VSA+BFA < 320 ........................................................................................... 205
   9.2.5. Case2: TFA+VSA+BFA = 320 (Rolling Scrolling) .............................................................. 206
   9.3. MCU to memory write/read direction ........................................................................................... 207
10. Tearing Effect Output................................................................................................................................. 209
    10.1. Tearing Effect Line Modes............................................................................................................ 209
    10.2. Tearing Effect Line Timings.......................................................................................................... 210
11. Sleep Out – Command and Self-Diagnostic Functions of the Display Module......................................... 211
    11.1. Register loading Detection........................................................................................................... 211
    11.2. Functionality Detection................................................................................................................. 212
12. Power ON/OFF Sequence ........................................................................................................................ 213
    12.1. Case 1 – RESX line is held High or Unstable by Host at Power ON........................................... 213
    12.2. Case 2 – RESX line is held Low by Host at Power ON ............................................................... 214
    12.3. Uncontrolled Power Off ................................................................................................................ 215
13. Power Level Definition .............................................................................................................................. 216
    13.1. Power Levels................................................................................................................................ 216
    13.2. Power Flow Chart......................................................................................................................... 217
14. Gamma Curves Selection ......................................................................................................................... 218
    14.1. Gamma Default Values (for NW type LC) .................................................................................... 218
    14.2. Gamma Curves ............................................................................................................................ 219
    a-Si TFT LCD Single Chip Driver
    240RGBx320 Resolution and 262K color ILI9341
    The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
    reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
    Page 6 of 239
    14.2.1. Gamma Curve 1 (GC0), applies the function y=x2.2
    .......................................................... 219
    14.3. Gamma Curves ............................................................................................................................ 220
    14.3.1. Grayscale Voltage Generation........................................................................................... 220
    14.3.2. Positive Gamma Correction............................................................................................... 221
    14.3.3. Negative Gamma Correction............................................................................................. 222
15. Reset ......................................................................................................................................................... 223
    15.1. Registers ...................................................................................................................................... 223
    15.2. Output Pins, I/O Pins.................................................................................................................... 224
    15.3. Input Pins ..................................................................................................................................... 224
    15.4. Reset Timing ................................................................................................................................ 225
16. Configuration of Power Supply Circuit ...................................................................................................... 226
17. NV Memory Programming Flow................................................................................................................ 227
18. Electrical Characteristics........................................................................................................................... 229
    18.1. Absolute Maximum Ratings ......................................................................................................... 229
    18.2. DC Characteristics ....................................................................................................................... 230
    19.2.1. General DC Characteristics............................................................................................... 230
    18.3. AC Characteristics ....................................................................................................................... 232
    19.3.1. Display Parallel 18/16/9/8-bit Interface Timing Characteristics (8080-Ⅰ system) ........... 232
    19.3.2. Display Parallel 18/16/9/8-bit Interface Timing Characteristics(8080-Ⅱ system) ............ 234
    19.3.3. Display Serial Interface Timing Characteristics (3-line SPI system) ................................. 236
    19.3.4. Display Serial Interface Timing Characteristics (4-line SPI system) ................................. 237
    19.3.5. Parallel 18/16/6-bit RGB Interface Timing Characteristics................................................ 238
19. Revision History ........................................................................................................................................ 239
    a-Si TFT LCD Single Chip Driver
    240RGBx320 Resolution and 262K color ILI9341
    The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
    reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
    Page 7 of 239
20. Introduction
    ILI9341 is a 262,144-color single-chip SOC driver for a-TFT liquid crystal display with resolution of 240RGBx320
    dots, comprising a 720-channel source driver, a 320-channel gate driver, 172,800 bytes GRAM for graphic
    display data of 240RGBx320 dots, and power supply circuit.
    ILI9341 supports parallel 8-/9-/16-/18-bit data bus MCU interface, 6-/16-/18-bit data bus RGB interface and
    3-/4-line serial peripheral interface (SPI). The moving picture area can be specified in internal GRAM by window
    address function. The specified window area can be updated selectively, so that moving picture can be
    displayed simultaneously independent of still picture area.
    ILI9341 can operate with 1.65V ~ 3.3V I/O interface voltage and an incorporated voltage follower circuit to
    generate voltage levels for driving an LCD. ILI9341 supports full color, 8-color display mode and sleep mode for
    precise power control by software and these features make the ILI9341 an ideal LCD driver for medium or small
    size portable products such as digital cellular phones, smart phone, MP3 and PMP where long battery life is a
    major concern.
21. Features
     Display resolution: [240xRGB](H) x 320(V)
     Output:
    720 source outputs
    320 gate outputs
    Common electrode output (VCOM)
     a-TFT LCD driver with on-chip full display RAM: 172,800 bytes
     System Interface
    8-bits, 9-bits, 16-bits, 18-bits interface with 8080-Ⅰ/8080- Ⅱ series MCU
    6-bits, 16-bits, 18-bits RGB interface with graphic controller
    3-line / 4-line serial interface
     Display mode:
    Full color mode (Idle mode OFF): 262K-color (selectable color depth mode by software)
    Reduce color mode (Idle mode ON): 8-color
     Power saving mode:
    Sleep mode
     On chip functions:
    VCOM generator and adjustment
    Timing generator
    Oscillator
    DC/DC converter
    Line/frame inversion
    1 preset Gamma curve with separate RGB Gamma correction
     Content Adaptive Brightness Control
     MTP (3 times):
    8-bits for ID1, ID2, ID3
    7-bits for VCOM adjustment
    a-Si TFT LCD Single Chip Driver
    240RGBx320 Resolution and 262K color ILI9341
    The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
    reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
    Page 8 of 239
    Low -power consumption architecture
    Low operating power supplies:
    VDDI = 1.65V ~ 3.3V (logic)
    VCI = 2.5V ~ 3.3V (analog)
    LCD Voltage drive:
    Source/VCOM power supply voltage
    AVDD - GND = 4.5V ~ 5.5V
    VCL - GND = -2.0V ~ -3.0V
    Gate driver output voltage
    VGH - GND = 10.0V ~ 20.0V
    VGL - GND = -5.0V ~ -15.0V
    VGH - VGL 3 ≦ 2V
    VCOM driver output voltage
    VCOMH = 3.0V ~ (AVDD – 0.5)V
    VCOML = (VCL+0.5)V ~ 0V
    VCOMH - VCOML ≦ 6.0V
     Operate temperature range: -40℃ to 85℃
    a-Si TFT LCD storage capacitor : Cst on Common structure only
    a-Si TFT LCD Single Chip Driver
    240RGBx320 Resolution and 262K color ILI9341
    The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
    reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
    Page 9 of 239
22. Block Diagram
    8/9/16/18-bit
    MCU I/F
    3/4 Serial I/F
    6/16/18-bit
    RGB I/F
    CSX
    WRX
    RDX
    D/CX
    D[17:0]
    SDA
    VSYNC
    HSYNC
    DOTCLK
    RESX
    IM[3:0]
    EXTC
    DUMMY
    VDDI
    Regulator
    RC-OSC. Timing
    Controller
    Charge-pump Power Circuit
    GVDD
    C11P
    VCI
    C11M
    AVDD
    C12P
    C12M
    VCL
    C22P
    C22M
    VGH
    VGL
    VCOM
    Generator
    VCOM
    Index
    Register
    (IR)
    Control
    Register
    (CR)
    18
    8
    Graphics
    Operation
    18
    Read
    Latch
    18
    18
    Write
    Latch
    Graphics RAM
    (GRAM)
    18 18
    Address
    Counter
    (AC)
    LCD
    Source
    Driver
    Grayscale
    Reference
    Voltage
    V63 ~ V0
    S720 ~ S1
    LCD
    Gate
    Driver
    G320 ~ G1
    VSSA
    VCORE
    C21P
    C21M
    DE
    CABC
    Block
    TE
    18
    4
    VSSC
    SDO
    LED
    Controller LEDPWM
    LEDON
    VDDI_LED
    a-Si TFT LCD Single Chip Driver
    240RGBx320 Resolution and 262K color ILI9341
    The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
    reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
    Page 10 of 239
23. Pin Descriptions
    Power Supply Pins
    Pin Name I/O Type Descriptions
    VDDI I P Low voltage power supply for interface logic circuits (1.65 ~ 3.3 V)
    VDDI_LED I Power supply for LED driver interface. (1.65 ~ 3.3 V)
    If LED driver is not used, fix this pin at VDDI.
    VCI I Analog Power High voltage power supply for analog circuit blocks (2.5 ~ 3.3 V)
    Vcore O Digital Power
    Regulated Low voltage level for interface circuits
    Connect a capacitor for stabilization.
    Don’t apply any external power to this pad
    VSS3 I I/O Ground System ground level for I/O circuits.
    VSS I Digital Ground System ground level for logic blocks
    VSSA I Analog Ground System ground level for analog circuit blocks
    Connect to VSS on the FPC to prevent noise.
    VSSC I Analog Ground System ground level for analog circuit blocks
    Connect to VSS on the FPC to prevent noise
    Interface Logic Signals
    Pin Name I/O Type Descriptions
    IM[3:0] I (VDDI/VSS)

- Select the MCU interface mode
  DB Pin in use IM3 IM2 IM1 IM0 MCU-Interface Mode
  Register/Content GRAM
  0 0 0 0
  80 MCU 8-bit bus
  interface Ⅰ
  D[7:0] D[7:0]
  0 0 0 1
  80 MCU 16-bit bus
  interface Ⅰ
  D[7:0] D[15:0]
  0 0 1 0
  80 MCU 9-bit bus
  interface Ⅰ
  D[7:0] D[8:0]
  0 0 1 1
  80 MCU 18-bit bus
  interface Ⅰ
  D[7:0] D[17:0]
  0 1 0 1
  3-wire 9-bit data serial
  interface Ⅰ
  SDA: In/OUT
  0 1 1 0
  4-wire 8-bit data serial
  interface Ⅰ
  SDA: In/OUT
  1 0 0 0
  80 MCU 16-bit bus
  interface Ⅱ
  D[8:1]
  D[17:10],
  D[8:1]
  1 0 0 1
  80 MCU 8-bit bus
  interface Ⅱ
  D[17:10] D[17:10]
  1 0 1 0
  80 MCU 18-bit bus
  interface Ⅱ
  D[8:1] D[17:0]
  1 0 1 1
  80 MCU 9-bit bus
  interface Ⅱ
  D[17:10] D[17:9]
  1 1 0 1
  3-wire 9-bit data serial
  interface Ⅱ
  SDI: In
  SDO: Out
  1 1 1 0
  4-wire 8-bit data serial
  interface Ⅱ
  SDI: In
  SDO: Out
  MPU Parallel interface bus and serial interface select
  If use RGB Interface must select serial interface.

* : Fix this pin at VDDI or VSS.
  a-Si TFT LCD Single Chip Driver
  240RGBx320 Resolution and 262K color ILI9341
  The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
  reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
  Page 11 of 239
  RESX I MCU
  (VDDI/VSS)
  This signal will reset the device and must be applied to properly
  initialize the chip.
  Signal is active low.
  EXTC I MCU
  (VDDI/VSS)
  Extended command set enable.
  Low: extended command set is discarded.
  High: extended command set is accepted.
  Please connect EXTC to VDDI to read/write extended registers
  (RB0h~RCFh, RE0h~RFFh)
  CSX I MCU
  (VDDI/VSS)
  Chip select input pin (“Low” enable).
  This pin can be permanently fixed “Low” in MPU interface mode only.
* note1,2
  D/CX (SCL) I MCU
  (VDDI/VSS)
  This pin is used to select “Data or Command” in the parallel interface
  or 4-wire 8-bit serial data interface.
  When DCX = ’1’, data is selected.
  When DCX = ’0’, command is selected.
  This pin is used serial interface clock in 3-wire 9-bit / 4-wire 8-bit
  serial data interface.
  If not used, this pin should be connected to VDDI or VSS.
  RDX I MCU
  (VDDI/VSS)
  8080- /8080 Ⅰ -Ⅱ system (RDX): Serves as a read signal and MCU
  read data at the rising edge.
  Fix to VDDI level when not in use.
  WRX
  (D/CX) I MCU
  (VDDI/VSS)

- 8080- /8080 Ⅰ -Ⅱ system (WRX): Serves as a write signal and
  writes data at the rising edge.
- 4-line system (D/CX): Serves as command or parameter select.
  Fix to VDDI level when not in use.
  D[17:0] I/O MCU
  (VDDI/VSS)
  18-bit parallel bi-directional data bus for MCU system and RGB
  interface mode
  Fix to VSS level when not in use
  SDI/SDA I/O MCU
  (VDDI/VSS)
  When IM[3] : Low, Serial in/out signal.
  When IM[3] : High, Serial input signal.
  The data is applied on the rising edge of the SCL signal.
  If not used, fix this pin at VDDI or VSS.
  SDO O MCU
  (VDDI/VSS)
  Serial output signal.
  The data is outputted on the falling edge of the SCL signal.
  If not used, open this pin
  TE O MCU
  (VDDI/VSS)
  Tearing effect output pin to synchronize MPU to frame writing,
  activated by S/W command. When this pin is not activated, this pin is
  low.
  If not used, open this pin.
  DOTCLK I MCU
  (VDDI/VSS)
  Dot clock signal for RGB interface operation.
  Fix to VDDI or VSS level when not in use.
  VSYNC I MCU
  (VDDI/VSS)
  Frame synchronizing signal for RGB interface operation.
  Fix to VDDI or VSS level when not in use.
  HSYNC I MCU
  (VDDI/VSS)
  Line synchronizing signal for RGB interface operation.
  Fix to VDDI or VSS level when not in use.
  DE I MCU
  (VDDI/VSS)
  Data enable signal for RGB interface operation.
  Fix to VDDI or VSS level when not in use.
  a-Si TFT LCD Single Chip Driver
  240RGBx320 Resolution and 262K color ILI9341
  The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
  reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
  Page 12 of 239
  Note.

1. If CSX is connected to VSS in Parallel interface mode, there will be no abnormal visible effect to the display module.
   Also there will be no restriction on using the Parallel Read/Write protocols, Power On/Off Sequences or other functions.
   Furthermore there will be no influence to the Power Consumption of the display module.
2. When CSX=’1’, there is no influence to the parallel and serial interface.
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 13 of 239
   LCD Driver Input/Output Pins
   Pin Name I/O Type Descriptions
   S720~S1 O Source Source output signals..
   Leave the pin to open when not in use.
   G320~G1 O Gate Gate output signals.
   Leave the pin to open when not in use.
   AVDD O
   Power
   Stabilizing
   capacitor
   Output voltage of 1st step up circuit (2 x VCI). Input voltage to 2nd step up
   circuit. Generated power output pad for source driver block. Connect this
   pad to the capacitor for stabilization.
   VGH O
   Power
   Stabilizing
   capacitor
   Power supply for the gate driver.
   Adjust the VGH level with the BT[2:0] bits.
   Connect this pad with a stabilizing capacitor.
   VGL O
   Power
   Stabilizing
   capacitor
   Power supply for the gate driver.
   Adjust the VGL level with the BT[2:0] bits.
   Connect this pad with a stabilizing capacitor.
   VCL 0
   Power
   Stabilizing
   capacitor
   Power supply for VCOML.
   VCL = 0~ - VCI
   Connect this pad with a stabilizing capacitor.
   C11P, C11M
   C12P, C12M
   P Stabilizing
   capacitor Connect the charge-pumping capacitor for generating AVDD level.
   C21P, C21M
   C22P, C22M
   P Stabilizing
   capacitor Connect the charge-pumping capacitor for generating VGH, VGL level.
   GVDD O High reference voltage for grayscale voltage generator.
   Internal register can be used to adjust the voltage.
   VCOM O
   Power supply pad for the TFT- display counter electrode.
   Charge recycling method is used with VCI and VSSA voltage.
   Connect this pad to the TFT-display counter electrode.
   LEDPWM O Output pin for PWM (Pulse Width Modulation) signal of LED driving.
   If not used, open this pad.
   LEDON O Output pin for enabling LED driving.
   If not used, open this pad.
   Test Pins
   Pin Name I/O Type Descriptions
   DUMMY - Open Input pads used only for test purpose at IC-side.
   During normal operation, leave these pads open.
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 14 of 239
   Liquid crystal power supply specifications Table
   No. Item Description
   1 TFT Source Driver 720 pins (240 x RGB)
   2 TFT Gate Driver 320 pins
   3 TFT Display’s Capacitor Structure Cst structure only (Cs on Common)
   S1 ~ S720 V0 ~ V63 grayscales
   4 Liquid Crystal Drive Output G1 ~ G320 VGH - VGL
   VCOM VCOMH - VCOML: Amplitude = electronic volumes
   VDDI 1.65V ~ 3.30V 5 Input Voltage VCI 2.50V ~ 3.30V
   AVDD 4.5V ~ 5.5V
   VGH 10.0V ~ 20.0V
   VGL -5.0V ~ -15.0V
   VCL -1.9V ~ -3.0V
   6 Liquid Crystal Drive Voltages
   VGH - VGL Max. 32.0V
   AVDD VCI x2,
   VGH VCI x6, x7
   VGL VCI x-5, x-6, 7 Internal Step-up Circuits
   VCL VCI x-1
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 15 of 239
3. Pad Arrangement and Coordination
   Face Up
   View)
   (Bump
   x
   y
   …………………
   …………………….
   1 0
   1
   0
   2
   0
   3
   0
   4
   0
   5
   0
   6
   0
   7
   0
   8
   0
   9
   0
   0
   1
   0
   1
   1
   0
   2
   1
   0
   3
   1
   0
   4
   1
   0
   5
   1
   0
   6
   1
   0
   7
   1
   0
   8
   1
   0
   9
   1
   0
   0
   2
   0
   1
   2
   0
   2
   2
   0
   3
   2
   ………………… …………………….
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 16 of 239
   No. Pad name X Y No. Pad name X Y No. Pad name X Y No. Pad name X Y
   1 DUMMY -7292.5 -248 51 C12M -4292.5 -248 101 VSSA -1292.5 -248 151 LEDPWM 2245 -248
   2 DUMMY -7232.5 -248 52 C12M -4232.5 -248 102 VSSA -1232.5 -248 152 LEDON 2330 -248
   3 VCOM -7172.5 -248 53 C11P -4172.5 -248 103 VSSA -1172.5 -248 153 VDDI_LED 2402.5 -248
   4 VCOM -7112.5 -248 54 C11P -4112.5 -248 104 VSSA -1112.5 -248 154 VDDI_LED 2462.5 -248
   5 VCOM -7052.5 -248 55 C11P -4052.5 -248 105 VSSA -1052.5 -248 155 DB[18]\_Dummy 2535 -248
   6 VCOM -6992.5 -248 56 C11P -3992.5 -248 106 DUMMY -992.5 -248 156 DB[19]\_Dummy 2620 -248
   7 VCOM -6932.5 -248 57 C11P -3932.5 -248 107 VGS -932.5 -248 157 DB[20]\_Dummy 2705 -248
   8 VCOM -6872.5 -248 58 C11P -3872.5 -248 108 VGS -872.5 -248 158 DB[21]\_Dummy 2790 -248
   9 VCOM -6812.5 -248 59 C11P -3812.5 -248 109 EXTC -812.5 -248 159 DB[22]\_Dummy 2875 -248
   10 VCOM -6752.5 -248 60 C11M -3752.5 -248 110 IM<3> -752.5 -248 160 DB[23]\_Dummy 2960 -248
   11 DUMMY -6692.5 -248 61 C11M -3692.5 -248 111 IM<2> -692.5 -248 161 DUMMY 3032.5 -248
   12 C22P -6632.5 -248 62 C11M -3632.5 -248 112 IM<1> -632.5 -248 162 VDDI 3092.5 -248
   13 C22P -6572.5 -248 63 C11M -3572.5 -248 113 IM<0> -572.5 -248 163 VDDI 3152.5 -248
   14 C22M -6512.5 -248 64 C11M -3512.5 -248 114 RESX -512.5 -248 164 VDDI 3212.5 -248
   15 C22M -6452.5 -248 65 C11M -3452.5 -248 115 CSX -452.5 -248 165 VDDI 3272.5 -248
   16 C21P -6392.5 -248 66 C11M -3392.5 -248 116 DCX -392.5 -248 166 VDDI 3332.5 -248
   17 C21P -6332.5 -248 67 (GND) -3332.5 -248 117 WRX -332.5 -248 167 VDDI 3392.5 -248
   18 C21M -6272.5 -248 68 (GND) -3272.5 -248 118 RDX -272.5 -248 168 VDDI 3452.5 -248
   19 C21M -6212.5 -248 69 (GND) -3212.5 -248 119 DUMMY -212.5 -248 169 Vcore 3512.5 -248
   20 VGH -6152.5 -248 70 (GND) -3152.5 -248 120 VSYNC -152.5 -248 170 Vcore 3572.5 -248
   21 VGH -6092.5 -248 71 (GND) -3092.5 -248 121 HSYNC -92.5 -248 171 Vcore 3632.5 -248
   22 VGH -6032.5 -248 72 (GND) -3032.5 -248 122 ENABL -32.5 -248 172 Vcore 3692.5 -248
   23 VGH -5972.5 -248 73 (GND) -2972.5 -248 123 DOTCLK 27.5 -248 173 Vcore 3752.5 -248
   24 VGH -5912.5 -248 74 VCI -2912.5 -248 124 DUMMY 87.5 -248 174 Vcore 3812.5 -248
   25 DUMMY -5852.5 -248 75 VCI -2842.5 -248 125 SDA 160 -248 175 Vcore 3872.5 -248
   26 VGL -5792.5 -248 76 VCI -2792.5 -248 126 DB[0] 245 -248 176 Vcore 3932.5 -248
   27 VGL -5732.5 -248 77 VCI -2732.5 -248 127 DB[1] 330 -248 177 Vcore 3992.5 -248
   28 VGL -5672.5 -248 78 VCI -2672.5 -248 128 DB[2] 415 -248 178 Vcore 4052.5 -248
   29 VGL -5612.5 -248 79 VCI -2612.5 -248 129 DB[3] 500 -248 179 Vcore 4112.5 -248
   30 VGL -5552.5 -248 80 VCI -2552.5 -248 130 DUMMY 572.5 -248 180 Vcore 4172.5 -248
   31 VGL -5492.5 -248 81 VCI -2492.5 -248 131 DB[4] 645 -248 181 Vcore 4232.5 -248
   32 AVDD -5432.5 -248 82 VSS3 -2432.5 -248 132 DB[5] 730 -248 182 Vcore 4292.5 -248
   33 AVDD -5372.5 -248 83 VSS3 -2372.5 -248 133 DB[6] 815 -248 183 DUMMY 4352.5 -248
   34 AVDD -5312.5 -248 84 VSS3 -2312.5 -248 134 DB[7] 900 -248 184 GVDD 4412.5 -248
   35 AVDD -5252.5 -248 85 VSS -2252.5 -248 135 DUMMY 972.5 -248 185 GVDD 4472.5 -248
   36 AVDD -5192.5 -248 86 VSS -2192.5 -248 136 DB[8] 1045 -248 186 GVDD 4532.5 -248
   37 AVDD -5132.5 -248 87 VSS -2132.5 -248 137 DB[9] 1130 -248 187 GVDD 4592.5 -248
   38 AVDD -5072.5 -248 88 VSS -2072.5 -248 138 DB[10] 1215 -248 188 DUMMY 4652.5 -248
   39 C12P -5012.5 -248 89 VSS -2012.5 -248 139 DB[11] 1300 -248 189 DUMMY 4712.5 -248
   40 C12P -4952.5 -248 90 VSS -1952.5 -248 140 DUMMY 1372.5 -248 190 VCL 4772.5 -248
   41 C12P -4892.5 -248 91 VSSC -1892.5 -248 141 DB[12] 1445 -248 191 VCL 4832.5 -248
   42 C12P -4832.5 -248 92 VSSC -1832.5 -248 142 DB[13] 1530 -248 192 VCL 4892.5 -248
   43 C12P -4772.5 -248 93 VSSC -1772.5 -248 143 DB[14] 1615 -248 193 VCL 4952.5 -248
   44 C12P -4712.5 -248 94 VSSC -1712.5 -248 144 DB[15] 1700 -248 194 VCL 5012.5 -248
   45 C12P -4652.5 -248 95 VSSC -1652.5 -248 145 DUMMY 1772.5 -248 195 VCL 5072.5 -248
   46 C12M -4592.5 -248 96 VSSC -1592.5 -248 146 DB[16] 1845 -248 196 VCL 5132.5 -248
   47 C12M -4532.5 -248 97 VSSC -1532.5 -248 147 DB[17] 1930 -248 197 VCL 5192.5 -248
   48 C12M -4472.5 -248 98 VSSA -1472.5 -248 148 DUMMY 2002.5 -248 198 DUMMY 5252.5 -248
   49 C12M -4412.5 -248 99 VSSA -1412.5 -248 149 TE 2075 -248 199 DUMMY 5312.5 -248
   50 C12M -4352.5 -248 100 VSSA -1352.5 -248 150 SDO 2160 -248 200 DUMMY 5372.5 -248
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 17 of 239
   No. Pad name X Y No. Pad name X Y No. Pad name X Y No. Pad name X Y
   201 DUMMY 5432.5 -248 251 G32 7147 224 301 G132 6447 224 351 G232 5747 224
   202 DUMMY 5492.5 -248 252 G34 7133 93 302 G134 6433 93 352 G234 5733 93
   203 DUMMY 5552.5 -248 253 G36 7119 224 303 G136 6419 224 353 G236 5719 224
   204 DUMMY 5612.5 -248 254 G38 7105 93 304 G138 6405 93 354 G238 5705 93
   205 DUMMY 5672.5 -248 255 G40 7091 224 305 G140 6391 224 355 G240 5691 224
   206 (GND) 5732.5 -248 256 G42 7077 93 306 G142 6377 93 356 G242 5677 93
   207 (GND) 5792.5 -248 257 G44 7063 224 307 G144 6363 224 357 G244 5663 224
   208 (GND) 5852.5 -248 258 G46 7049 93 308 G146 6349 93 358 G246 5649 93
   209 (GND) 5912.5 -248 259 G48 7035 224 309 G148 6335 224 359 G248 5635 224
   210 (GND) 5972.5 -248 260 G50 7021 93 310 G150 6321 93 360 G250 5621 93
   211 (GND) 6032.5 -248 261 G52 7007 224 311 G152 6307 224 361 G252 5607 224
   212 (GND) 6092.5 -248 262 G54 6993 93 312 G154 6293 93 362 G254 5593 93
   213 (GND) 6152.5 -248 263 G56 6979 224 313 G156 6279 224 363 G256 5579 224
   214 DUMMY 6212.5 -248 264 G58 6965 93 314 G158 6265 93 364 G258 5565 93
   215 DUMMY 6272.5 -248 265 G60 6951 224 315 G160 6251 224 365 G260 5551 224
   216 DUMMY 6332.5 -248 266 G62 6937 93 316 G162 6237 93 366 G262 5537 93
   217 DUMMY 6392.5 -248 267 G64 6923 224 317 G164 6223 224 367 G264 5523 224
   218 DUMMY 6452.5 -248 268 G66 6909 93 318 G166 6209 93 368 G266 5509 93
   219 DUMMY 6512.5 -248 269 G68 6895 224 319 G168 6195 224 369 G268 5495 224
   220 DUMMY 6572.5 -248 270 G70 6881 93 320 G170 6181 93 370 G270 5481 93
   221 DUMMY 6632.5 -248 271 G72 6867 224 321 G172 6167 224 371 G272 5467 224
   222 DUMMY 6692.5 -248 272 G74 6853 93 322 G174 6153 93 372 G274 5453 93
   223 VCOM 6752.5 -248 273 G76 6839 224 323 G176 6139 224 373 G276 5439 224
   224 VCOM 6812.5 -248 274 G78 6825 93 324 G178 6125 93 374 G278 5425 93
   225 VCOM 6872.5 -248 275 G80 6811 224 325 G180 6111 224 375 G280 5411 224
   226 VCOM 6932.5 -248 276 G82 6797 93 326 G182 6097 93 376 G282 5397 93
   227 VCOM 6992.5 -248 277 G84 6783 224 327 G184 6083 224 377 G284 5383 224
   228 VCOM 7052.5 -248 278 G86 6769 93 328 G186 6069 93 378 G286 5369 93
   229 VCOM 7112.5 -248 279 G88 6755 224 329 G188 6055 224 379 G288 5355 224
   230 VCOM 7172.5 -248 280 G90 6741 93 330 G190 6041 93 380 G290 5341 93
   231 DUMMY 7232.5 -248 281 G92 6727 224 331 G192 6027 224 381 G292 5327 224
   232 DUMMY 7292.5 -248 282 G94 6713 93 332 G194 6013 93 382 G294 5313 93
   233 DUMMY 7399 224 283 G96 6699 224 333 G196 5999 224 383 G296 5299 224
   234 DUMMY 7385 93 284 G98 6685 93 334 G198 5985 93 384 G298 5285 93
   235 DUMMY 7371 224 285 G100 6671 224 335 G200 5971 224 385 G300 5271 224
   236 G2 7357 93 286 G102 6657 93 336 G202 5957 93 386 G302 5257 93
   237 G4 7343 224 287 G104 6643 224 337 G204 5943 224 387 G304 5243 224
   238 G6 7329 93 288 G106 6629 93 338 G206 5929 93 388 G306 5229 93
   239 G8 7315 224 289 G108 6615 224 339 G208 5915 224 389 G308 5215 224
   240 G10 7301 93 290 G110 6601 93 340 G210 5901 93 390 G310 5201 93
   241 G12 7287 224 291 G112 6587 224 341 G212 5887 224 391 G312 5187 224
   242 G14 7273 93 292 G114 6573 93 342 G214 5873 93 392 G314 5173 93
   243 G16 7259 224 293 G116 6559 224 343 G216 5859 224 393 G316 5159 224
   244 G18 7245 93 294 G118 6545 93 344 G218 5845 93 394 G318 5145 93
   245 G20 7231 224 295 G120 6531 224 345 G220 5831 224 395 G320 5131 224
   246 G22 7217 93 296 G122 6517 93 346 G222 5817 93 396 S720 5075 93
   247 G24 7203 224 297 G124 6503 224 347 G224 5803 224 397 S719 5061 224
   248 G26 7189 93 298 G126 6489 93 348 G226 5789 93 398 S718 5047 93
   249 G28 7175 224 299 G128 6475 224 349 G228 5775 224 399 S717 5033 224
   250 G30 7161 93 300 G130 6461 93 350 G230 5761 93 400 S716 5019 93
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 18 of 239
   No. Pad name X Y No. Pad name X Y No. Pad name X Y No. Pad name X Y
   401 S715 5005 224 451 S665 4305 224 501 S615 3605 224 551 S565 2905 224
   402 S714 4991 93 452 S664 4291 93 502 S614 3591 93 552 S564 2891 93
   403 S713 4977 224 453 S663 4277 224 503 S613 3577 224 553 S563 2877 224
   404 S712 4963 93 454 S662 4263 93 504 S612 3563 93 554 S562 2863 93
   405 S711 4949 224 455 S661 4249 224 505 S611 3549 224 555 S561 2849 224
   406 S710 4935 93 456 S660 4235 93 506 S610 3535 93 556 S560 2835 93
   407 S709 4921 224 457 S659 4221 224 507 S609 3521 224 557 S559 2821 224
   408 S708 4907 93 458 S658 4207 93 508 S608 3507 93 558 S558 2807 93
   409 S707 4893 224 459 S657 4193 224 509 S607 3493 224 559 S557 2793 224
   410 S706 4879 93 460 S656 4179 93 510 S606 3479 93 560 S556 2779 93
   411 S705 4865 224 461 S655 4165 224 511 S605 3465 224 561 S555 2765 224
   412 S704 4851 93 462 S654 4151 93 512 S604 3451 93 562 S554 2751 93
   413 S703 4837 224 463 S653 4137 224 513 S603 3437 224 563 S553 2737 224
   414 S702 4823 93 464 S652 4123 93 514 S602 3423 93 564 S552 2723 93
   415 S701 4809 224 465 S651 4109 224 515 S601 3409 224 565 S551 2709 224
   416 S700 4795 93 466 S650 4095 93 516 S600 3395 93 566 S550 2695 93
   417 S699 4781 224 467 S649 4081 224 517 S599 3381 224 567 S549 2681 224
   418 S698 4767 93 468 S648 4067 93 518 S598 3367 93 568 S548 2667 93
   419 S697 4753 224 469 S647 4053 224 519 S597 3353 224 569 S547 2653 224
   420 S696 4739 93 470 S646 4039 93 520 S596 3339 93 570 S546 2639 93
   421 S695 4725 224 471 S645 4025 224 521 S595 3325 224 571 S545 2625 224
   422 S694 4711 93 472 S644 4011 93 522 S594 3311 93 572 S544 2611 93
   423 S693 4697 224 473 S643 3997 224 523 S593 3297 224 573 S543 2597 224
   424 S692 4683 93 474 S642 3983 93 524 S592 3283 93 574 S542 2583 93
   425 S691 4669 224 475 S641 3969 224 525 S591 3269 224 575 S541 2569 224
   426 S690 4655 93 476 S640 3955 93 526 S590 3255 93 576 S540 2555 93
   427 S689 4641 224 477 S639 3941 224 527 S589 3241 224 577 S539 2541 224
   428 S688 4627 93 478 S638 3927 93 528 S588 3227 93 578 S538 2527 93
   429 S687 4613 224 479 S637 3913 224 529 S587 3213 224 579 S537 2513 224
   430 S686 4599 93 480 S636 3899 93 530 S586 3199 93 580 S536 2499 93
   431 S685 4585 224 481 S635 3885 224 531 S585 3185 224 581 S535 2485 224
   432 S684 4571 93 482 S634 3871 93 532 S584 3171 93 582 S534 2471 93
   433 S683 4557 224 483 S633 3857 224 533 S583 3157 224 583 S533 2457 224
   434 S682 4543 93 484 S632 3843 93 534 S582 3143 93 584 S532 2443 93
   435 S681 4529 224 485 S631 3829 224 535 S581 3129 224 585 S531 2429 224
   436 S680 4515 93 486 S630 3815 93 536 S580 3115 93 586 S530 2415 93
   437 S679 4501 224 487 S629 3801 224 537 S579 3101 224 587 S529 2401 224
   438 S678 4487 93 488 S628 3787 93 538 S578 3087 93 588 S528 2387 93
   439 S677 4473 224 489 S627 3773 224 539 S577 3073 224 589 S527 2373 224
   440 S676 4459 93 490 S626 3759 93 540 S576 3059 93 590 S526 2359 93
   441 S675 4445 224 491 S625 3745 224 541 S575 3045 224 591 S525 2345 224
   442 S674 4431 93 492 S624 3731 93 542 S574 3031 93 592 S524 2331 93
   443 S673 4417 224 493 S623 3717 224 543 S573 3017 224 593 S523 2317 224
   444 S672 4403 93 494 S622 3703 93 544 S572 3003 93 594 S522 2303 93
   445 S671 4389 224 495 S621 3689 224 545 S571 2989 224 595 S521 2289 224
   446 S670 4375 93 496 S620 3675 93 546 S570 2975 93 596 S520 2275 93
   447 S669 4361 224 497 S619 3661 224 547 S569 2961 224 597 S519 2261 224
   448 S668 4347 93 498 S618 3647 93 548 S568 2947 93 598 S518 2247 93
   449 S667 4333 224 499 S617 3633 224 549 S567 2933 224 599 S517 2233 224
   450 S666 4319 93 500 S616 3619 93 550 S566 2919 93 600 S516 2219 93
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 19 of 239
   No. Pad name X Y No. Pad name X Y No. Pad name X Y No. Pad name X Y
   601 S515 2205 224 651 S465 1505 224 701 S415 805 224 751 S365 105 224
   602 S514 2191 93 652 S464 1491 93 702 S414 791 93 752 S364 91 93
   603 S513 2177 224 653 S463 1477 224 703 S413 777 224 753 S363 77 224
   604 S512 2163 93 654 S462 1463 93 704 S412 763 93 754 S362 63 93
   605 S511 2149 224 655 S461 1449 224 705 S411 749 224 755 S361 49 224
   606 S510 2135 93 656 S460 1435 93 706 S410 735 93 756 S360 -49 93
   607 S509 2121 224 657 S459 1421 224 707 S409 721 224 757 S359 -63 224
   608 S508 2107 93 658 S458 1407 93 708 S408 707 93 758 S358 -77 93
   609 S507 2093 224 659 S457 1393 224 709 S407 693 224 759 S357 -91 224
   610 S506 2079 93 660 S456 1379 93 710 S406 679 93 760 S356 -105 93
   611 S505 2065 224 661 S455 1365 224 711 S405 665 224 761 S355 -119 224
   612 S504 2051 93 662 S454 1351 93 712 S404 651 93 762 S354 -133 93
   613 S503 2037 224 663 S453 1337 224 713 S403 637 224 763 S353 -147 224
   614 S502 2023 93 664 S452 1323 93 714 S402 623 93 764 S352 -161 93
   615 S501 2009 224 665 S451 1309 224 715 S401 609 224 765 S351 -175 224
   616 S500 1995 93 666 S450 1295 93 716 S400 595 93 766 S350 -189 93
   617 S499 1981 224 667 S449 1281 224 717 S399 581 224 767 S349 -203 224
   618 S498 1967 93 668 S448 1267 93 718 S398 567 93 768 S348 -217 93
   619 S497 1953 224 669 S447 1253 224 719 S397 553 224 769 S347 -231 224
   620 S496 1939 93 670 S446 1239 93 720 S396 539 93 770 S346 -245 93
   621 S495 1925 224 671 S445 1225 224 721 S395 525 224 771 S345 -259 224
   622 S494 1911 93 672 S444 1211 93 722 S394 511 93 772 S344 -273 93
   623 S493 1897 224 673 S443 1197 224 723 S393 497 224 773 S343 -287 224
   624 S492 1883 93 674 S442 1183 93 724 S392 483 93 774 S342 -301 93
   625 S491 1869 224 675 S441 1169 224 725 S391 469 224 775 S341 -315 224
   626 S490 1855 93 676 S440 1155 93 726 S390 455 93 776 S340 -329 93
   627 S489 1841 224 677 S439 1141 224 727 S389 441 224 777 S339 -343 224
   628 S488 1827 93 678 S438 1127 93 728 S388 427 93 778 S338 -357 93
   629 S487 1813 224 679 S437 1113 224 729 S387 413 224 779 S337 -371 224
   630 S486 1799 93 680 S436 1099 93 730 S386 399 93 780 S336 -385 93
   631 S485 1785 224 681 S435 1085 224 731 S385 385 224 781 S335 -399 224
   632 S484 1771 93 682 S434 1071 93 732 S384 371 93 782 S334 -413 93
   633 S483 1757 224 683 S433 1057 224 733 S383 357 224 783 S333 -427 224
   634 S482 1743 93 684 S432 1043 93 734 S382 343 93 784 S332 -441 93
   635 S481 1729 224 685 S431 1029 224 735 S381 329 224 785 S331 -455 224
   636 S480 1715 93 686 S430 1015 93 736 S380 315 93 786 S330 -469 93
   637 S479 1701 224 687 S429 1001 224 737 S379 301 224 787 S329 -483 224
   638 S478 1687 93 688 S428 987 93 738 S378 287 93 788 S328 -497 93
   639 S477 1673 224 689 S427 973 224 739 S377 273 224 789 S327 -511 224
   640 S476 1659 93 690 S426 959 93 740 S376 259 93 790 S326 -525 93
   641 S475 1645 224 691 S425 945 224 741 S375 245 224 791 S325 -539 224
   642 S474 1631 93 692 S424 931 93 742 S374 231 93 792 S324 -553 93
   643 S473 1617 224 693 S423 917 224 743 S373 217 224 793 S323 -567 224
   644 S472 1603 93 694 S422 903 93 744 S372 203 93 794 S322 -581 93
   645 S471 1589 224 695 S421 889 224 745 S371 189 224 795 S321 -595 224
   646 S470 1575 93 696 S420 875 93 746 S370 175 93 796 S320 -609 93
   647 S469 1561 224 697 S419 861 224 747 S369 161 224 797 S319 -623 224
   648 S468 1547 93 698 S418 847 93 748 S368 147 93 798 S318 -637 93
   649 S467 1533 224 699 S417 833 224 749 S367 133 224 799 S317 -651 224
   650 S466 1519 93 700 S416 819 93 750 S366 119 93 800 S316 -665 93
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 20 of 239
   No. Pad name X Y No. Pad name X Y No. Pad name X Y No. Pad name X Y
   801 S315 -679 224 851 S265 -1379 224 901 S215 -2079 224 951 S165 -2779 224
   802 S314 -693 93 852 S264 -1393 93 902 S214 -2093 93 952 S164 -2793 93
   803 S313 -707 224 853 S263 -1407 224 903 S213 -2107 224 953 S163 -2807 224
   804 S312 -721 93 854 S262 -1421 93 904 S212 -2121 93 954 S162 -2821 93
   805 S311 -735 224 855 S261 -1435 224 905 S211 -2135 224 955 S161 -2835 224
   806 S310 -749 93 856 S260 -1449 93 906 S210 -2149 93 956 S160 -2849 93
   807 S309 -763 224 857 S259 -1463 224 907 S209 -2163 224 957 S159 -2863 224
   808 S308 -777 93 858 S258 -1477 93 908 S208 -2177 93 958 S158 -2877 93
   809 S307 -791 224 859 S257 -1491 224 909 S207 -2191 224 959 S157 -2891 224
   810 S306 -805 93 860 S256 -1505 93 910 S206 -2205 93 960 S156 -2905 93
   811 S305 -819 224 861 S255 -1519 224 911 S205 -2219 224 961 S155 -2919 224
   812 S304 -833 93 862 S254 -1533 93 912 S204 -2233 93 962 S154 -2933 93
   813 S303 -847 224 863 S253 -1547 224 913 S203 -2247 224 963 S153 -2947 224
   814 S302 -861 93 864 S252 -1561 93 914 S202 -2261 93 964 S152 -2961 93
   815 S301 -875 224 865 S251 -1575 224 915 S201 -2275 224 965 S151 -2975 224
   816 S300 -889 93 866 S250 -1589 93 916 S200 -2289 93 966 S150 -2989 93
   817 S299 -903 224 867 S249 -1603 224 917 S199 -2303 224 967 S149 -3003 224
   818 S298 -917 93 868 S248 -1617 93 918 S198 -2317 93 968 S148 -3017 93
   819 S297 -931 224 869 S247 -1631 224 919 S197 -2331 224 969 S147 -3031 224
   820 S296 -945 93 870 S246 -1645 93 920 S196 -2345 93 970 S146 -3045 93
   821 S295 -959 224 871 S245 -1659 224 921 S195 -2359 224 971 S145 -3059 224
   822 S294 -973 93 872 S244 -1673 93 922 S194 -2373 93 972 S144 -3073 93
   823 S293 -987 224 873 S243 -1687 224 923 S193 -2387 224 973 S143 -3087 224
   824 S292 -1001 93 874 S242 -1701 93 924 S192 -2401 93 974 S142 -3101 93
   825 S291 -1015 224 875 S241 -1715 224 925 S191 -2415 224 975 S141 -3115 224
   826 S290 -1029 93 876 S240 -1729 93 926 S190 -2429 93 976 S140 -3129 93
   827 S289 -1043 224 877 S239 -1743 224 927 S189 -2443 224 977 S139 -3143 224
   828 S288 -1057 93 878 S238 -1757 93 928 S188 -2457 93 978 S138 -3157 93
   829 S287 -1071 224 879 S237 -1771 224 929 S187 -2471 224 979 S137 -3171 224
   830 S286 -1085 93 880 S236 -1785 93 930 S186 -2485 93 980 S136 -3185 93
   831 S285 -1099 224 881 S235 -1799 224 931 S185 -2499 224 981 S135 -3199 224
   832 S284 -1113 93 882 S234 -1813 93 932 S184 -2513 93 982 S134 -3213 93
   833 S283 -1127 224 883 S233 -1827 224 933 S183 -2527 224 983 S133 -3227 224
   834 S282 -1141 93 884 S232 -1841 93 934 S182 -2541 93 984 S132 -3241 93
   835 S281 -1155 224 885 S231 -1855 224 935 S181 -2555 224 985 S131 -3255 224
   836 S280 -1169 93 886 S230 -1869 93 936 S180 -2569 93 986 S130 -3269 93
   837 S279 -1183 224 887 S229 -1883 224 937 S179 -2583 224 987 S129 -3283 224
   838 S278 -1197 93 888 S228 -1897 93 938 S178 -2597 93 988 S128 -3297 93
   839 S277 -1211 224 889 S227 -1911 224 939 S177 -2611 224 989 S127 -3311 224
   840 S276 -1225 93 890 S226 -1925 93 940 S176 -2625 93 990 S126 -3325 93
   841 S275 -1239 224 891 S225 -1939 224 941 S175 -2639 224 991 S125 -3339 224
   842 S274 -1253 93 892 S224 -1953 93 942 S174 -2653 93 992 S124 -3353 93
   843 S273 -1267 224 893 S223 -1967 224 943 S173 -2667 224 993 S123 -3367 224
   844 S272 -1281 93 894 S222 -1981 93 944 S172 -2681 93 994 S122 -3381 93
   845 S271 -1295 224 895 S221 -1995 224 945 S171 -2695 224 995 S121 -3395 224
   846 S270 -1309 93 896 S220 -2009 93 946 S170 -2709 93 996 S120 -3409 93
   847 S269 -1323 224 897 S219 -2023 224 947 S169 -2723 224 997 S119 -3423 224
   848 S268 -1337 93 898 S218 -2037 93 948 S168 -2737 93 998 S118 -3437 93
   849 S267 -1351 224 899 S217 -2051 224 949 S167 -2751 224 999 S117 -3451 224
   850 S266 -1365 93 900 S216 -2065 93 950 S166 -2765 93 1000 S116 -3465 93
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 21 of 239
   No. Pad name X Y No. Pad name X Y No. Pad name X Y No. Pad name X Y
   1001 S115 -3479 224 1051 S65 -4179 224 1101 S15 -4879 224 1151 G249 -5621 224
   1002 S114 -3493 93 1052 S64 -4193 93 1102 S14 -4893 93 1152 G247 -5635 93
   1003 S113 -3507 224 1053 S63 -4207 224 1103 S13 -4907 224 1153 G245 -5649 224
   1004 S112 -3521 93 1054 S62 -4221 93 1104 S12 -4921 93 1154 G243 -5663 93
   1005 S111 -3535 224 1055 S61 -4235 224 1105 S11 -4935 224 1155 G241 -5677 224
   1006 S110 -3549 93 1056 S60 -4249 93 1106 S10 -4949 93 1156 G239 -5691 93
   1007 S109 -3563 224 1057 S59 -4263 224 1107 S9 -4963 224 1157 G237 -5705 224
   1008 S108 -3577 93 1058 S58 -4277 93 1108 S8 -4977 93 1158 G235 -5719 93
   1009 S107 -3591 224 1059 S57 -4291 224 1109 S7 -4991 224 1159 G233 -5733 224
   1010 S106 -3605 93 1060 S56 -4305 93 1110 S6 -5005 93 1160 G231 -5747 93
   1011 S105 -3619 224 1061 S55 -4319 224 1111 S5 -5019 224 1161 G229 -5761 224
   1012 S104 -3633 93 1062 S54 -4333 93 1112 S4 -5033 93 1162 G227 -5775 93
   1013 S103 -3647 224 1063 S53 -4347 224 1113 S3 -5047 224 1163 G225 -5789 224
   1014 S102 -3661 93 1064 S52 -4361 93 1114 S2 -5061 93 1164 G223 -5803 93
   1015 S101 -3675 224 1065 S51 -4375 224 1115 S1 -5075 224 1165 G221 -5817 224
   1016 S100 -3689 93 1066 S50 -4389 93 1116 G319 -5131 93 1166 G219 -5831 93
   1017 S99 -3703 224 1067 S49 -4403 224 1117 G317 -5145 224 1167 G217 -5845 224
   1018 S98 -3717 93 1068 S48 -4417 93 1118 G315 -5159 93 1168 G215 -5859 93
   1019 S97 -3731 224 1069 S47 -4431 224 1119 G313 -5173 224 1169 G213 -5873 224
   1020 S96 -3745 93 1070 S46 -4445 93 1120 G311 -5187 93 1170 G211 -5887 93
   1021 S95 -3759 224 1071 S45 -4459 224 1121 G309 -5201 224 1171 G209 -5901 224
   1022 S94 -3773 93 1072 S44 -4473 93 1122 G307 -5215 93 1172 G207 -5915 93
   1023 S93 -3787 224 1073 S43 -4487 224 1123 G305 -5229 224 1173 G205 -5929 224
   1024 S92 -3801 93 1074 S42 -4501 93 1124 G303 -5243 93 1174 G203 -5943 93
   1025 S91 -3815 224 1075 S41 -4515 224 1125 G301 -5257 224 1175 G201 -5957 224
   1026 S90 -3829 93 1076 S40 -4529 93 1126 G299 -5271 93 1176 G199 -5971 93
   1027 S89 -3843 224 1077 S39 -4543 224 1127 G297 -5285 224 1177 G197 -5985 224
   1028 S88 -3857 93 1078 S38 -4557 93 1128 G295 -5299 93 1178 G195 -5999 93
   1029 S87 -3871 224 1079 S37 -4571 224 1129 G293 -5313 224 1179 G193 -6013 224
   1030 S86 -3885 93 1080 S36 -4585 93 1130 G291 -5327 93 1180 G191 -6027 93
   1031 S85 -3899 224 1081 S35 -4599 224 1131 G289 -5341 224 1181 G189 -6041 224
   1032 S84 -3913 93 1082 S34 -4613 93 1132 G287 -5355 93 1182 G187 -6055 93
   1033 S83 -3927 224 1083 S33 -4627 224 1133 G285 -5369 224 1183 G185 -6069 224
   1034 S82 -3941 93 1084 S32 -4641 93 1134 G283 -5383 93 1184 G183 -6083 93
   1035 S81 -3955 224 1085 S31 -4655 224 1135 G281 -5397 224 1185 G181 -6097 224
   1036 S80 -3969 93 1086 S30 -4669 93 1136 G279 -5411 93 1186 G179 -6111 93
   1037 S79 -3983 224 1087 S29 -4683 224 1137 G277 -5425 224 1187 G177 -6125 224
   1038 S78 -3997 93 1088 S28 -4697 93 1138 G275 -5439 93 1188 G175 -6139 93
   1039 S77 -4011 224 1089 S27 -4711 224 1139 G273 -5453 224 1189 G173 -6153 224
   1040 S76 -4025 93 1090 S26 -4725 93 1140 G271 -5467 93 1190 G171 -6167 93
   1041 S75 -4039 224 1091 S25 -4739 224 1141 G269 -5481 224 1191 G169 -6181 224
   1042 S74 -4053 93 1092 S24 -4753 93 1142 G267 -5495 93 1192 G167 -6195 93
   1043 S73 -4067 224 1093 S23 -4767 224 1143 G265 -5509 224 1193 G165 -6209 224
   1044 S72 -4081 93 1094 S22 -4781 93 1144 G263 -5523 93 1194 G163 -6223 93
   1045 S71 -4095 224 1095 S21 -4795 224 1145 G261 -5537 224 1195 G161 -6237 224
   1046 S70 -4109 93 1096 S20 -4809 93 1146 G259 -5551 93 1196 G159 -6251 93
   1047 S69 -4123 224 1097 S19 -4823 224 1147 G257 -5565 224 1197 G157 -6265 224
   1048 S68 -4137 93 1098 S18 -4837 93 1148 G255 -5579 93 1198 G155 -6279 93
   1049 S67 -4151 224 1099 S17 -4851 224 1149 G253 -5593 224 1199 G153 -6293 224
   1050 S66 -4165 93 1100 S16 -4865 93 1150 G251 -5607 93 1200 G151 -6307 93
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 22 of 239
   No. Pad name X Y No. Pad name X Y
   1201 G149 -6321 224 1251 G49 -7021 224
   1202 G147 -6335 93 1252 G47 -7035 93
   1203 G145 -6349 224 1253 G45 -7049 224
   1204 G143 -6363 93 1254 G43 -7063 93
   1205 G141 -6377 224 1255 G41 -7077 224
   1206 G139 -6391 93 1256 G39 -7091 93
   1207 G137 -6405 224 1257 G37 -7105 224
   1208 G135 -6419 93 1258 G35 -7119 93
   1209 G133 -6433 224 1259 G33 -7133 224
   1210 G131 -6447 93 1260 G31 -7147 93
   1211 G129 -6461 224 1261 G29 -7161 224
   1212 G127 -6475 93 1262 G27 -7175 93
   1213 G125 -6489 224 1263 G25 -7189 224
   1214 G123 -6503 93 1264 G23 -7203 93
   1215 G121 -6517 224 1265 G21 -7217 224
   1216 G119 -6531 93 1266 G19 -7231 93
   1217 G117 -6545 224 1267 G17 -7245 224
   1218 G115 -6559 93 1268 G15 -7259 93
   1219 G113 -6573 224 1269 G13 -7273 224
   1220 G111 -6587 93 1270 G11 -7287 93
   1221 G109 -6601 224 1271 G9 -7301 224
   1222 G107 -6615 93 1272 G7 -7315 93
   1223 G105 -6629 224 1273 G5 -7329 224
   1224 G103 -6643 93 1274 G3 -7343 93
   1225 G101 -6657 224 1275 G1 -7357 224
   1226 G99 -6671 93 1276 DUMMY -7371 93
   1227 G97 -6685 224 1277 DUMMY -7385 224
   1228 G95 -6699 93 1278 DUMMY -7399 93
   1229 G93 -6713 224
   1230 G91 -6727 93
   1231 G89 -6741 224
   1232 G87 -6755 93
   1233 G85 -6769 224
   1234 G83 -6783 93
   1235 G81 -6797 224
   1236 G79 -6811 93
   1237 G77 -6825 224
   1238 G75 -6839 93
   1239 G73 -6853 224
   1240 G71 -6867 93
   1241 G69 -6881 224
   1242 G67 -6895 93 Alignment mark X Y
   1243 G65 -6909 224 Left COG Align -7480 225
   1244 G63 -6923 93 Right COG Align 7480 225
   1245 G61 -6937 224
   1246 G59 -6951 93
   1247 G57 -6965 224
   1248 G55 -6979 93
   1249 G53 -6993 224
   1250 G51 -7007 93
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 23 of 239
   BUMP Size
   Input Pad
   (1 ~ 232)
   
   
   Output Pad
   (233 ~ 1278)
   




a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 24 of 239 6. Block Function Description
MCU System Interface
ILI9341 provides four kinds of MCU system interface with 8080- /8080 Ⅰ - Ⅱ series parallel interface and
3-/4-line serial interface. The selection of the given interfaces are done by external IM [3:0] pins and shown
as below:
Pins in use IM3 IM2 IM1 IM0 MCU-Interface Mode
Register/Content GRAM
0 0 0 0 8080 MCU 8-bit bus interface Ⅰ D[7:0] D[7:0],WRX,RDX,CSX,D/CX
0 0 0 1 8080 MCU 16-bit bus interface Ⅰ D[7:0] D[15:0],WRX,RDX,CSX,D/CX
0 0 1 0 8080 MCU 9-bit bus interface Ⅰ D[7:0] D[8:0],WRX,RDX,CSX,D/CX
0 0 1 1 8080 MCU 18-bit bus interface Ⅰ D[7:0] D[17:0],WRX,RDX,CSX,D/CX
0 1 0 1 3-wire 9-bit data serial interface Ⅰ SCL,SDA,CSX
0 1 1 0 4-wire 8-bit data serial interface Ⅰ SCL,SDA,D/CX,CSX
1 0 0 0 8080 MCU 16-bit bus interface Ⅱ D[8:1] D[17:10],D[8:1],WRX,RDX,CSX,D/CX
1 0 0 1 8080 MCU 8-bit bus interface Ⅱ D[17:10] D[17:10],WRX,RDX,CSX,D/CX
1 0 1 0 8080 MCU 18-bit bus interface Ⅱ D[8:1] D[17:0],WRX,RDX,CSX,D/CX
1 0 1 1 8080 MCU 9-bit bus interface Ⅱ D[17:10] D[17:9],WRX,RDX,CSX,D/CX
1 1 0 1 3-wire 9-bit data serial interface Ⅱ SCL,SDI,SDO, CSX
1 1 1 0 4-wire 8-bit data serial interface Ⅱ SCL,SDI,D/CX,SDO, CSX
In 8080-Ⅰ/8080-Ⅱ series parallel interface, the registers are accessed by the D[17:0] data pins.
8080-Ⅰ Series 8080-Ⅱ Series
CSX D/CX RDX WRX CSX D/CX RDX WRX
Operation
“L” “L” “H” “L” “L” “H” Write command
“L” “H” “H” “L” “H” “H” Read parameter
“L” “H” “H” “L” “H” “H” Write parameter
Parallel RGB Interface
ILI9341 also supports the RGB interface for displaying a moving picture. When the RGB interface is selected,
display operation is synchronized with externally signals, VSYNC, HSYNC, and DOTCLK and input display
data is written in synchronization with these signals according to the polarity of enable signal (DE).
Graphic RAM (GRAM)
GRAM is a graphic RAM to store display data. GRAM size is 172,800 bytes with 18 bits per pixel for a
maximum 240(RGB) x320 dot graphic display.
Grayscale Voltage Generating Circuit
Grayscale voltage generating circuit generates a liquid crystal drive voltage, which corresponds to grayscale
level set in the gamma correction register. ILI9341 can display maximum 262,144 colors.
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 25 of 239
Power Supply Circuit
The LCD drive power supply circuit generates the voltage levels as GVDD, VGH, VGL and VCOM for driving
TFT LCD panel.
Timing controller
The timing controller generates all the timing signals for display and GRAM access.
Oscillator
ILI9341 incorporates RC oscillator circuit and output a stable output frequency for operation.
Panel Driver Circuit
Liquid crystal display driver circuit consists of 720-output source driver (S1~S720), 320-output gate driver
(G1~G320), and VCOM signal.
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 26 of 239 7. Function Description
7.1. MCU interfaces
ILI9341 provides the 8-/9-/16-/18-bit parallel system interface for 8080- /8080 Ⅰ -Ⅱ series, and 3-/4-line serial
system interface for serial data input. The input system interface is selected by external pins IM [3:0] and the bit
formal per pixel color order is selected by DBI [2:0] bits of 3Ah register.
7.1.1. MCU interface selection
The selection of interface is done by setting external pins IM [3:0] as shown in the following table.
Pins in use IM3 IM2 IM1 IM0 MCU-Interface Mode
Register/Content GRAM
0 0 0 0 8080 MCU 8-bit bus interface Ⅰ D[7:0] D[7:0],WRX,RDX,CSX,D/CX
0 0 0 1 8080 MCU 16-bit bus interface Ⅰ D[7:0] D[15:0] ,WRX,RDX,CSX,D/CX
0 0 1 0 8080 MCU 9-bit bus interface Ⅰ D[7:0] D[8:0] ,WRX,RDX,CSX,D/CX
0 0 1 1 8080 MCU 18-bit bus interface Ⅰ D[7:0] D[17:0] ,WRX,RDX,CSX,D/CX
0 1 0 1 3-wire 9-bit data serial interface Ⅰ SCL,SDA,CSX
0 1 1 0 4-wire 8-bit data serial interface Ⅰ SCL,SDA,D/CX,CSX
1 0 0 0 8080 MCU 16-bit bus interface Ⅱ D[8:1] D[17:10],D[8:1],WRX,RDX,CSX,D/CX
1 0 0 1 8080 MCU 8-bit bus interface Ⅱ D[17:10] D[17:10],WRX,RDX,CSX,D/CX
1 0 1 0 8080 MCU 18-bit bus interface Ⅱ D[8:1] D[17:0],WRX,RDX,CSX,D/CX
1 0 1 1 8080 MCU 9-bit bus interface Ⅱ D[17:10] D[17:9],WRX,RDX,CSX,D/CX
1 1 0 1 3-wire 9-bit data serial interface Ⅱ SCL,SDI,SDO, CSX
1 1 1 0 4-wire 8-bit data serial interface Ⅱ SCL,SDI,D/CX,SDO, CSX
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 27 of 239
7.1.2. 8080-Ⅰ Series Parallel Interface
ILI9341 can be accessed via 8-/9-/16-/18-bit MCU 8080-Ⅰ series parallel interface. The chip-select CSX (active
low) is used to enable or disable ILI9341 chip. The RESX (active low) is an external reset signal. WRX is the
parallel data write strobe, RDX is the parallel data read strobe and D[17:0] is parallel data bus.
ILI9341 latches the input data at the rising edge of WRX signal. The D/CX is the signal of data/command
selection. When D/CX=’1’, D [17:0] bits are display RAM data or command’s parameters. When D/CX=’0’, D
[17:0] bits are commands.
The 8080-Ⅰ series bi-directional interface can be used for communication between the MCU controller and LCD
driver chip. The 8080-Ⅰ Interface selection is done when IM3 pin is low state (VSS level). Interface bus width
can be selected by IM [2:0] bits.
The selection of 8080-Ⅰ series parallel interface is shown as the table in the following.
IM3 IM2 IM1 IM0 MCU-Interface Mode CSX WRX RDX D/CX Function
“L” “H” “L” Write command code.
“L” “H” “H” Read internal status.
“L” “H” “H” Write parameter or display data.
0 0 0 0 8080 MCU 8-bit bus interface Ⅰ
“L” “H” “H” Reads parameter or display data.
“L” “H” “L” Write command code.
“L” “H” “H” Read internal status.
“L” “H” “H” Write parameter or display data.
0 0 0 1 8080 MCU 16-bit bus interface Ⅰ
“L” “H” “H” Reads parameter or display data.
“L” “H” “L” Write command code.
“L” “H” “H” Read internal status.
“L” “H” “H” Write parameter or display data.
0 0 1 0 8080 MCU 9-bit bus interface Ⅰ
“L” “H” “H” Reads parameter or display data.
“L” “H” “L” Write command code.
“L” “H” “H” Read internal status.
“L” “H” “H” Write parameter or display data.
0 0 1 1 8080 MCU 18-bit bus interface Ⅰ
“L” “H” “H” Reads parameter or display data.
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 28 of 239
7.1.3. Write Cycle Sequence
The WRX signal is driven from high to low and then be pulled back to high during the write cycle. The host
processor provides information during the write cycle when the display module captures the information from
host processor on the rising edge of WRX. When the D/CX signal is driven to low level, then input data on the
interface is interpreted as command information. The D/CX signal also can be pulled high level when the data on
the interface is RAM data or command’s parameter.
The following figure shows a write cycle for the 8080-Ⅰ MCU interface.
Note: WRX is an unsynchronized signal (It can be stopped) Interface ILI9341 Host
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 29 of 239
7.1.4. Read Cycle Sequence
The RDX signal is driven from high to low and then allowed to be pulled back to high during the read cycle. The
display module provides information to the host processor during the read cycle while the host processor reads
the display module information on the rising edge of RDX signal. When the D/CX signal is driven to low level,
then input data on the interface is interpreted as command. The D/CX signal also can be pulled high level when
the data on the interface is RAM data or command parameter.
The following figure shows the read cycle for the 8080-Ⅰ MCU interface.
`
Note: RDX is an unsynchronized signal (It can be stopped). Interface Host ILI9341
Note: Read data is only valid when the D/CX input is pulled high. If D/CX is driven low during read then the
display information outputs will be High-Z.
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 30 of 239
7.1.5. 8080-Ⅱ Series Parallel Interface
ILI9341 can be accessed via 8-/9-/16-/18-bit MCU 8080-Ⅱ series parallel interface. The chip-select CSX (active
low) is used to enable or disable ILI9341 chip. The RESX (active low) is an external reset signal. WRX is the
parallel data write strobe, RDX is the parallel data read strobe and D[17:0] is parallel data bus.
ILI9341 latches the input data at the rising edge of WRX signal. The D/CX is the signal of data/command
selection. When D/CX=’1’, D [17:0] bits are display RAM data or command’s parameters. When D/CX=’0’, D
[17:0] bits are commands.
The 8080-Ⅱ series bi-directional interface can be used for communication between the MCU controller and LCD
driver chip. The 8080-Ⅱ Interface selection is done when IM3 pin is high state (VDDI level). Interface bus width
can be selected by IM [2:0] bits.
The selection of 8080-Ⅱ series parallel interface is shown as the table in the following.
IM3 IM2 IM1 IM0 MCU-Interface Mode CSX WRX RDX D/CX Function
“L” “H” “L” Write command code.
“L” “H” “H” Read internal status.
“L” “H” “H” Write parameter or display data.
1 0 0 0 8080 MCU 16-bit bus interface Ⅱ
“L” “H” “H” Reads parameter or display data.
“L” “H” “L” Write command code.
“L” “H” “H” Read internal status.
“L” “H” “H” Write parameter or display data.
1 0 0 1 8080 MCU 8-bit bus interface Ⅱ
“L” “H” “H” Reads parameter or display data.
“L” “H” “L” Write command code.
“L” “H” “H” Read internal status.
“L” “H” “H” Write parameter or display data.
1 0 1 0 8080 MCU 18-bit bus interface Ⅱ
“L” “H” “H” Reads parameter or display data.
“L” “H” “L” Write command code.
“L” “H” “H” Read internal status.
“L” “H” “H” Write parameter or display data.
1 0 1 1 8080 MCU 9-bit bus interface Ⅱ
“L” “H” “H” Reads parameter or display data.
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 31 of 239
7.1.6. Write Cycle Sequence
The WRX signal is driven from high to low and then be pulled back to high during the write cycle. The host
processor provides information during the write cycle when the display module captures the information from
host processor on the rising edge of WRX. When the D/CX signal is driven to low level, then input data on the
interface is interpreted as command information. The D/CX signal also can be pulled high level when the data on
the interface is RAM data or command’s parameter.
The following figure shows a write cycle for the 8080-Ⅱ MCU interface.
Note: WRX is an unsynchronized signal (It can be stopped) Interface ILI9341 Host
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 32 of 239
7.1.7. Read Cycle Sequence
The RDX signal is driven from high to low and then allowed to be pulled back to high during the read cycle. The
display module provides information to the host processor during the read cycle while the host processor reads
the display module information on the rising edge of RDX signal. When the D/CX signal is driven to low level,
then input data on the interface is interpreted as command. The D/CX signal also can be pulled high level when
the data on the interface is RAM data or command parameter.
The following figure shows the read cycle for the 8080-Ⅱ MCU interface.
Note: RDX is an unsynchronized signal (It can be stopped). Interface Host ILI9341
Note: Read data is only valid when the D/CX input is pulled high. If D/CX is driven low during read then the
display information outputs will be High-Z.
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 33 of 239
7.1.8. Serial Interface
The selection of interface is done by IM [3:0] bits. Please refer to the Table in the following.
IM3 IM2 IM1 IM0 MCU-Interface Mode CSX D/CX SCL Function
0 1 0 1 3-line serial interface “L” - Read/Write command, parameter or display data.
0 1 1 0 4-line serial interface “L” ‘H/L” Read/Write command, parameter or display data.
1 1 0 1 3-line serial interface “L” - Read/Write command, parameter or display data.
1 1 1 0 4-line serial interface “L” ‘H/L” Read/Write command, parameter or display data.
ILI9341 supplies 3-lines/ 9-bit and 4-line/8-bit bi-directional serial interfaces for communication between host
and ILI9341. The 3-line serial mode consists of the chip enable input (CSX), the serial clock input (SCL) and
serial data Input/Output (SDA or SDI/SDO). The 4-line serial mode consists of the Data/Command selection
input (D/CX), chip enable input (CSX), the serial clock input (SCL) and serial data Input/Output (SDA or
SDI/SDO) for data transmission. The data bus (D [17:0]), which are not used, must be connected to GND. Serial
clock (SCL) is used for interface with MCU only, so it can be stopped when no communication is necessary.
7.1.9. Write Cycle Sequence
The write mode of the interface means that host writes commands or data to ILI9341. The 3-lines serial data
packet contains a data/command select bit (D/CX) and a transmission byte. If the D/CX bit is “low”, the
transmission byte is interpreted as a command byte. If the D/CX bit is “high”, the transmission byte is stored as
the display data RAM (Memory write command), or command register as parameter.
Any instruction can be sent in any order to ILI9341 and the MSB is transmitted first. The serial interface is
initialized when CSX is high status. In this state, SCL clock pulse and SDA data are no effect. A falling edge on
CSX enables the serial interface and indicates the start of data transmission. See the detailed data format for
3-/4-line serial interface.
D/CX D7 D6 D5 D4 D3 D2 D1 D0
MSB LSB
Transmission byte may be Command or Data
D/CX 8-bit Transmission Byte D/CX 8-bit Transmission Byte
Data/Command select bit
Data Format for 3-line Serial Interface
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 34 of 239
D7 D6 D5 D4 D3 D2 D1 D0
MSB LSB
Transmission byte may be Command or Data
8-bit Transmission Byte 8-bit Transmission Byte 8-bit Transmission Byte
Data Format for 4-line Serial Interface
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 35 of 239
Host processor drives the CSX pin to low and starts by setting the D/CX bit on SDA. The bit is read by ILI9341
on the first rising edge of SCL signal. On the next falling edge of SCL, the MSB data bit (D7) is set on SDA by
the host. On the next falling edge of SCL, the next bit (D6) is set on SDA. If the optional D/CX signal is used, a
byte is eight read cycle width. The 3/4-line serial interface writes sequence described in the figure as below.
S TB P
0 D7 D6 D5 D4 D3 D2 D1 D0 D/C D7 D6 D5 D4 D3 D2 D1 D0
TB
CSX
SDA
SCL
Command Data / Command / Parameter
The CSX can be high level between the data and
next command.The SDA and SCL are invalid during
CSX is high level
Host
(MCU to Driver)
3-line Serial Interface Protocol
S T B P
D 7 D 6 D 5 D 4 D 3 D 2 D 7 D 6 D 5 D 4 D 3 D 2 D 1 D 0
T B
C S X
D /C X
S C L
C o m m a n d
C S X ca n b e "H " b e tw e e n co m m a n d /
co m m a n d a n d p a ra m e te r / co m m a n d . S C L a n d
S D A d u rin g C S X = "H " is in va lid .
S D A
0 T B D /C
D 1 D 0
4 -lin e S e ria l In te rfa c e P ro to c o l
D a ta / C o m m a n d / P a ra m e te r
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 36 of 239
7.1.10. Read Cycle Sequence
The read mode of interface means that the host reads register’s parameter or display data from ILI9341. The
host has to send a command (Read ID or register command) and then the following byte is transmitted in the
opposite direction. ILI9341 latches the SDA (input data) at the rising edges of SCL (serial clock), and then shifts
SDA (output data) at falling edges of SCL (serial clock). After the read status command has been sent, the SDA
line must be set to tri-state and no later than at the falling edge of SCL of the last bit. The read mode has three
types of transmitted command data (8-/24-/32-bit) according command code.
3-wire Serial Interface Protocol
TB P
D/C D7 D6 D5 D4 D3 D2 D1 D0
S TB S
D/C
3-wire Serial Protocol (for RDID1/RDID2/RDID3/0Ah/0Bh/0Ch/0Dh/0Eh/0Fh command: 8-bit read)
D7 D6 D5 D4 D3 D2 D1 D0
D/C D7 D6 D5 D4 D3 D2 D1 D0
D7 D6 D5 D4 D3 D2 D1 D0
D/C
CSX
SDA
SCL
SDA
SDO
Interface I
Interface II
Command Read Data Output
3-wire Serial Protocol (for RDDID command: 24-bit read)
TB P
D/C D7 D6 D5 D4 D3 D2 D1 D0
TB
CSX
SDA
S S
D/C
SCL
D/C D7 D6 D5 D4 D3 D2 D1 D0
D23 D22 D21 D2 D1 D0
SDA D/C
SDO
Dummy Clock Cycle
D23 D22 D21 D2 D1 D0 Interface I
Interface II
Command Multi-byte
Read Data Output
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 37 of 239
TB P
D/C D7 D6 D5 D4 D3 D2 D1 D0
TB
CSX
SDA
S S
D/C
3-wire Serial Protocol (for RDDST command: 32-bit read)
SCL
D/C D7 D6 D5 D4 D3 D2 D1 D0
D31 D30 D29 D2 D1 D0
SDA D/C
SDO
Dummy Clock Cycle
D31 D30 D29 D2 D1 D0 Interface I
Interface II
Command Multi-byte
Read Data Output
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 38 of 239
4-wire Serial Interface Protocol
TB P
D7 D6 D5 D4 D3 D2 D1 D0
S TB S
4-wire Serial Protocol (for RDID1/RDID2/RDID3/0Ah/0Bh/0Ch/0Dh/0Eh/0Fh command: 8-bit read)
D7 D6 D5 D4 D3 D2 D1 D0
D7 D6 D5 D4 D3 D2 D1 D0
D7 D6 D5 D4 D3 D2 D1 D0
CSX
SDA
SCL
SDI
SDO
Interface I
Interface II
Command Read Data Output
D/CX 0
4-wire Serial Protocol (for RDDID command: 24-bit read)
TB P
D7 D6 D5 D4 D3 D2 D1 D0
TB
CSX
SDA
S S
SCL
D7 D6 D5 D4 D3 D2 D1 D0
D23 D22 D21 D2 D1 D0
SDI
SDO
Dummy Clock Cycle
D23 D22 D21 D2 D1 D0 Interface I
Interface II
Command Multi-byte
Read Data Output
D/CX 0
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 39 of 239
TB P
D7 D6 D5 D4 D3 D2 D1 D0
TB
CSX
SDA
S S
4-wire Serial Protocol (for RDDST command: 32-bit read)
SCL
D7 D6 D5 D4 D3 D2 D1 D0
D31 D30 D29 D2 D1 D0
SDI
SDO
Dummy Clock Cycle
D31 D30 D29 D2 D1 D0 Interface I
Interface II
Command Multi-byte
Read Data Output
D/CX 0
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 40 of 239
7.1.11. Data Transfer Break and Recovery
If there is a break in data transmission by RESX pulse, while transferring a command or frame memory data or
multiple parameter command data, before Bit D0 of the byte has been completed, then the driver will reject the
previous bits and have reset the interface such that it will be ready to receive command data again when the
chip select pin (CSX) is activated after RESX have been high state.
S TB P
D/C D7 D6 D5 D4 D3 D2 D/C D7 D6 D5 D4 D3 D2 D1 D0
TB
CSX
RESX
SCL
Command /
Parameter / Data Command
The SCL and SDA during RESX=”L” is
invalid and next byte becomes command.
Wait for more than 10us
SDA
Driver
(MPU to Driver)
If there is a break in data transmission by CSX pulse, while transferring a command or frame memory data or
multiple parameter command data, before Bit D0 of the byte has been completed, then the driver will reject the
previous bits and have reset the interface such that it will be ready to receive the same byte re-transmitted when
the chip select pin (CSX) is next activated.
S TB P
D/C D7 D6 D5 D4 D/C D7 D6 D5 D4 D3 D2 D1 D0
TB
CSX
SDA
SCL
Break Data / Command / Parameter Data /
Command /
Parameter
Driver
(MPU to Driver)
If a two or more parameter command is being sent and a break occurs while sending any parameter before the
last one and if the host then sends a new command rather than continue to send the remained parameters that
was interrupted, then the parameters which had been successfully sent are stored and the parameter where the
break occurred is rejected. The interface is ready to receive next byte as shown below.
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 41 of 239
Command 1 Parameter 11 Parameter 12 Command 2
Command 1 Parameter 11 Parameter 12 Parameter 13
Break
Parameter11 is successfully sent, but Parameter12
is breaked and needed to be transfer again.
Command1 with first parameter (Parameter11) sould be excuted
again to write remained parameter (Parameter12 and Parameter13)
If a two or more parameter command is being sent and a break occurs by the other command before the last
one is sent, then the parameters which had been successfully sent are stored and the other parameter of that
command remains previous value.
Command 1 Parameter 11 Command 2
Parameter 11 Parameter 12 Parameter 13
Break Parameter11 is successfully sent, but other parameters
are not sent and broken by the other command.
Command1 with first parameter (Parameter11) sould be excuted
again to write remained parameter (Parameter12 and Parameter13)
Command 1
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 42 of 239
7.1.12. Data Transfer Pause
It will be possible when transferring a command, frame memory data or multiple parameter data to invoke a
pause in the data transmission. If the chip select pin (CSX) is released to high state after a whole byte of a frame
memory data or multiple parameter data has been completed, then ILI9341 will wait and continue the frame
memory data or parameter data transmission from the point where it was paused. If the chip select pin is
released after a whole byte of a command has been completed, then the display module will receive either the
command’s parameters (if appropriate) or a new command when the chip select pin is next enabled as shown
below.
This applies to the following 4 conditions:

1. Command-Pause-Command
2. Command-Pause-Parameter
3. Parameter-Pause-Command
4. Parameter-Pause-Parameter
   Command 1
   Parameter 11
   Command 2 Parameter 21 Parameter 22
   Pause
   Condition 1:
   The host transmits a new Command
   (Command 2) when a pause occurs
   after Command 1.
   Pause
   Condition 4:
   The host continues to transmit the remain
   parameter (Parameter 22) when a pause occurs
   after Parameter 21.
   Condition 2:
   The host continues to transmit the remain
   parameter (Parameter 11) when a pause occurs
   after Command 1.
   Command 3
   Condition 3:
   The host transmits a new command (Command
5. when a pause occurs after Parameter 11.
   Pause
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 43 of 239
   7.1.13. Serial Interface Pause (3_wire)
   S TB P
   0 D7 D6 D5 D4 D3 D2 D1 D0 D/C D7 D6 D5 D4 D3 D2 D1 D0
   TB
   CSX
   SDA
   SCL
   Command Data / Command / Parameter
   The CSX can be high level between the data and
   next command.The SDA and SCL are invalid during
   CSX is high level
   Host
   (MCU to Driver)
   7.1.14. Parallel Interface Pause
   D/CX
   RDX
   CSX
   WRX
   D[17:0] D17 to D0 D17 to D0
   Command / Parameter Pause Command / Parameter
   Pause
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 44 of 239
   7.1.15. Data Transfer Mode
   ILI9341 can provide two different kinds of color depth (16-bit/pixel and 18-bit/pixel) display data to the graphic
   RAM. The data format is described for each interface. Data can be downloaded to the frame memory by 2
   methods.
   7.1.16. Data Transfer Method 1
   The image data is sent to the frame memory in the successive frame writing, each time the frame memory is
   filled by image data, the frame memory pointer is reset to the start point and the next frame is written.
   Start Frame
   Memory Write
   Image Data
   Frame 1
   Image Data
   Frame 2
   Image Data
   Frame 3 Any Command
   Start Stop
   7.1.17. Data Transfer Method 2
   Image data is sent and at the end of each frame memory download, a command is sent to stop frame memory
   writing. Then start memory write command is sent, and a new frame is downloaded.
   Start Frame
   Memory
   Write
   Image Data
   Frame 1
   Any
   Command
   Start Frame
   Memory
   Write
   Image Data
   Frame 2
   Any
   Command
   Start Stop
   Any
   Command
   Note 1: These methods are applied to all data transfer color modes on both serial and parallel interfaces.
   Note 2: The frame memory can contain both odd and even number of pixels for both methods. Only complete
   pixel data will be stored in the frame memory.
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 45 of 239
   7.2. RGB Interface
   7.2.1. RGB Interface Selection
   ILI9341 has two kinds of RGB interface and these interfaces can be selected by RCM [1:0] bits. When RCM [1:0]
   bits are set to “10”, the DE mode is selected which utilizes VSYNC, HSYNC, DOTCLK, DE, D [17:0] pins; when
   RCM [1:0] bits are set to “11”, the SYNC mode is selected which utilizes which utilizes VSYNC, HSYNC,
   DOTCLK, D [17:0] pins. Using RGB interface must selection serial interface.
   ILI9341 supports several pixel formats that can be selected by DPI [2:0] bits of “Pixel Format Set (3Ah)” and RIM
   bit of RF6h command. The selection of a given interfaces is done by setting RCM [1:0] and DPI [2:0] as show in
   the following table.
   RCM[1:0] RIM DPI[2:0]
   RGB Interface
   Mode
   RGB Mode Used Pins
   1 0 0 1 1 0
   18-bit RGB interface
   (262K colors)
   VSYNC, HSYNC, DE, DOTCLK,D[17:0]
   1 0 0 1 0 1
   16-bit RGB interface
   (65K colors)
   VSYNC, HSYNC, DE, DOTCLK,
   D[17:13] & D[11:1]
   1 0 1 1 1 0
   6-bit RGB interface
   (262K colors)
   VSYNC, HSYNC, DE, DOTCLK, D[5:0]
   1 0 1 1 0 1
   6-bit RGB interface
   (65K colors)
   DE Mode
   Valid data is determined by the DE
   signal
   VSYNC, HSYNC, DE, DOTCLK, D[5:0]
   1 1 0 1 1 0
   18-bit RGB interface
   (262K colors)
   VSYNC, HSYNC, DOTCLK, D[17:0]
   1 1 0 1 0 1
   16-bit RGB interface
   (65K colors)
   VSYNC, HSYNC, DOTCLK,
   D[17:13] & D[11:1]
   1 1 1 1 1 0
   6-bit RGB interface
   (262K colors)
   VSYNC, HSYNC, DOTCLK, D[5:0]
   1 1 1 1 0 1
   6-bit RGB interface
   (65K colors)
   SYNC Mode
   In SYNC mode, DE signal is ignored;
   blanking porch is determined by B5h
   command.
   VSYNC, HSYNC, DOTCLK, D[5:0]
   18-bit data bus interface (D[17:0] is used) , DPI[2:0] = 110, and RIM=0
   D17 D16 D15 D14 D13 D12 D11 D10 D9 D8 D7 D6 D5 D4 D3 D2 D1 D0
   18bpp Frame Memory Write R[5] R[4] R[3] R[2] R[1] R[0] G[5] G[4] G[3] G[2] G[1] G[0] B[5] B[4] B[3] B[2] B[1] B[0]
   D17 D16 D15 D14 D13 D12 D11 D10 D9 D8 D7 D6 D5 D4 D3 D2 D1 D0
   16bpp Frame Memory Write R[2] R[1] R[0] G[5] G[4] G[3] G[2] G[1] G[0] B[4] B[3] B[2] B[1] B[0]
   D17 D5 D4 D3 D2 D1 D0
   18bpp Frame Memory Write R[5] R[4] R[3] R[2] R[1] R[0] G[5] G[4] G[3] G[2] G[1] G[0] B[5] B[4] B[3] B[2] B[1] B[0]
   16-bit data bus interface (D[17:13] & D[11:1] is used) , DPI[2:0] = 101, and RIM=0
   6-bit data bus interface (D[5:0] is used) , DPI[2:0] = 110, and RIM=1
   D5 D4 D3 D2 D1 D0 D5 D4 D3 D2 D1 D0
   D17 D5 D4 D3 D2 D1 D0
   16bpp Frame Memory Write R[4] R[3] R[2] R[1] R[0] G[5] G[4] G[3] G[2] G[1] G[0] B[4] B[3] B[2] B[1] B[0]
   6-bit data bus interface (D[5:0] is used) , DPI[2:0] = 101, and RIM=1
   D5 D4 D3 D2 D1 D0 D5 D4 D3 D2 D1 D0
   R[4] R[3]
   The LSB data of red/blue color depends on the EPF[1:0] setting.
   The LSB data of red/blue color depends on the EPF[1:0] setting.
   Pixel clock (DOTCLK) is running all the time without stopping and used to enter VSYNC, HSYNC, DE and D
   [17:0] states when there is a rising edge of the DOTCLK. Vertical synchronization (VSYNC) is used to tell when
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 46 of 239
   there is received a new frame of the display. This is low enable and its state is read to the display module by a
   rising edge of the DOTCLK signal.
   Horizontal synchronization (HSYNC) is used to tell when there is received a new line of the frame. This is low
   enable and its state is read to the display module by a rising edge of the DOTCLK signal.
   In DE mode, Data Enable (DE) is used to tell when there is received RGB information that should be transferred
   on the display. This is a high enable and its state is read to the display module by a rising edge of the DOTCLK
   signal. D [17:0] are used to tell what is the information of the image that is transferred on the display (When
   DE= ’0’ (low) and there is a rising edge of DOTCLK). D [17:0] can be ‘0’ (low) or ‘1’ (high). These lines are read
   by a rising edge of the DOTCLK signal. In SYNC mode, the valid display data in inputted in pixel unit via D [17:0]
   according to HFP/HBP settings of HSYNC signal and VFP/VBP setting of VSYNC. In both RGB interface modes,
   the input display data is written to GRAM first then outputs corresponding source voltage according the gray
   data from GRAM.
   Hsync HBP HAdr HFP
   Vsync VAdr VFP
   (VAdr + HAdr) - Period
   when valid display data are
   transferred from host to
   display module
   (Vsync + VBP) - Vertical interval when no valid
   display data is transferred from host to display
   (Hsync + HBP) – Horizontal interval when no
   valid display data is sent from host to display
   VFP -- Vertical interval when no valid display
   data is transferred from host to display
   HFP - Horizontal interval when no valid
   display data is sent from host to display
   VBP
   Parameters Symbols Condition Min. Typ. Max. Units
   Horizontal Synchronization Hsync 2 10 16 DOTCLK
   Horizontal Back Porch HBP 2 20 24 DOTCLK
   Horizontal Address HAdr - 240 - DOTCLK
   Horizontal Front Porch HFP 2 10 16 DOTCLK
   Vertical Synchronization Vsync 1 2 4 Line
   Vertical Back Porch VBP 1 2 - Line
   Vertical Address VAdr - 320 - Line
   Vertical Front Porch VFP 3 4 - Line
   Typical values are setting example when used with panel resolution 240 x 320 (QVGA), clock frequency 6.35MHz and frame
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 47 of 239
   frequency about 70Hz.
   Notes:

1) Vertical period (one frame) shall be equal to the sum of Vsync + VBP + VAdr + VFP.
2) Horizontal period (one line) shall be equal to the sum of Hsync + HBP + HAdr + HFP.
3) Control signals PCLK and Hsync shall be transmitted as specified at all times while valid pixels are transferred
   between the host processor and the display module.
   Also make sure that
   (Number of PCLK per 1 line) ≥ (Number of RTN clock) x Division ratio (DIV) x PCDIV
   Setting Example for Display Control Clock in RGB Interface Operation
   Register Display operation using DPI is in synchronization with internal clock PCLKD which is generated by dividing
   DOTCLK.
   PCDIV [5:0]: Number of DOTCLK during internal clock PCLKD’s high / low period. In units of 1 clock.
   PCDIV specifying DOTCLK’s division ratio, are determined so that difference between PCLKD’s frequency
   and internal oscillation clock 615KHz is the smallest. Set PCDIV follow the restriction
   (Number of PCLK in 1H) ≥ (Number of RTN clock) x Division ratio (DIV) x PCDIV.
   Setting Example: To set frame frequency to 70Hz:
   Internal Clock
   Internal Oscillation Clock: 615KHz
   DIV[1:0] = 2’b0 (x 1/1)
   RTN[4:0] = 5’h1b (27 clocks)
   FP = 7'h2 (2 lines), BP = 7'h2 (2 lines), NL = 6’h27 (320 lines)
   Frame Rate  70.30Hz
   DOTCLK
   HSYNC = 10 CLK
   HBP = 20 CLK
   HFP=10 CLK
   70Hz x (2 + 320 + 2) lines x (10 + 20 + 240 + 10) clocks = 6.35MHz
   DOTCLK frequency = 6.35MHz
   6.35 MHz / 615KHz = 10.32 I Set PCDIV so that PCLK is divided by 10.
   external fosc = 6.35 MHz / 10 = 635KHz
   PCDIV = [ 6.35MHz / 635KHz) / 2 ] - 1 = 4
   PCDIV[5:0] = 6’h04 (10 DOTCLK)
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 48 of 239
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 49 of 239
   7.2.2. RGB Interface Timing
   The timing chart of 18-/16-bit RGB interface mode is shown as below.
   HSYNC
   VSYNC
   DOTCLK
   ENABLE
   D[17:0]
   Back porch
   VLW>=1H
   1 frame
   Front porch
   Valid data
   HLW>=2DOTCLKs
   1H
   DTST>=HLW
   HSYNC
   DOTCLK
   ENABLE
   D[5:0]
   VLW : VSYNC Low Width
   HLW : HSYNC Low Width
   DTST : Data Transfer Startup Time
   R G B R G B B R G B
   DOTCLK
   PCLKD
   PCDIVH[3:0] PCDIVL[3:0]
   Note 1: The DE signal is not needed when RGB interface SYNC mode is selected.
   Note 2: VSPL=’0’, HSPL=’0’, DPL=’0’ and EPL=’0’ of “Interface Mode Control (B0h)” command.
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 50 of 239
   The timing chart of 6-bit RGB interface mode is shown as below:
   HSYNC
   VSYNC
   DOTCLK
   ENABLE
   D[5:0]
   Back porch
   VLW>=1H
   1 frame
   Front porch
   Valid data
   HLW>=2DOTCLKs
   1H
   DTST>=HLW
   HSYNC
   DOTCLK
   ENABLE
   D[5:0]
   VLW : VSYNC Low Width
   HLW : HSYNC Low Width
   DTST : Data Transfer Startup Time
   R G B R G B B R G B
   DOTCLK
   PCLKD
   PCDIVH[3:0] PCDIVL[3:0]
   Note 1: The DE signal is not needed when RGB interface SYNC mode is selected.
   Note 2: VSPL=’0’, HSPL=’0’, DPL=’0’ and EPL=’0’ of “Interface Mode Control (B0h)” command.
   Note 3: In 6-bit RGB interface mode, each dot of one pixel (R, G and B) is transferred in synchronization with
   DOTCLK.
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 51 of 239
   Note 4: In 6-bit RGB interface mode, set the cycles of VSYNC, HSYNC and DE to 3 multiples of DOTCLK.
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 52 of 239
   7.3. VSYNC Interface
   ILI9341 supports the VSYNC interface in synchronization with the frame-synchronizing signal VSYNC to display
   the moving picture with the 8080- / Ⅰ 8080-Ⅱ system interface. When the VSYNC interface is selected to display
   a moving picture, the minimum GRAM update speed is limited and the VSYNC interface is enabled by setting
   DM[1:0] = “10” and RM = “0”.
   MPU
   VSYNC
   nCS
   RS
   DB[17:0]
   nWR
   In the VSYNC mode, the display operation is synchronized with the internal clock and VSYNC input and the
   frame rate is determined by the pulse rate of VSYNC signal. All display data are stored in GRAM to minimize
   total data transfer required for moving picture display.
   Rewriting
   screen data
   Rewriting
   screen data
   VSYNC
   Write data to RAM
   through system
   interface
   Display operation
   synchronized with
   internal clocks
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 53 of 239
   The VSYNC interface has the minimum speed limitation of writing data to the internal GRAM via the system
   interface, which are calculated from the following formula.
   Internal clock frequency (fosc.) [Hz] = FrameFrequency x (DisplayLine (NL) + FrontPorch (VFP) + BackPorch
   (VBP)) x ClockCyclePerLines (RTN) x FrequencyFluctuation.
   Minimum RAM write speed [Hz] ＞
   [BackPorch(VBP) DisplayLines(NL) margins] Clocks per line (1/fosc)
   240 DisplayLines(NL)

- − × ×
  ×
  Note: When the RAM write operation does not start from the falling edge of VSYNC, the time from the falling
  edge of VSYNC until the start of RAM write operation must also be taken into account.
  An example of minimum GRAM writing speed and internal clock frequency in VSYNC interface mode is as
  below.
  [Example]
  Display size: 240 RGB × 320 lines
  Lines: 320 lines (NL = 100111)
  Back porch: 2 lines (VBP = 0000010)
  Front porch: 2 lines (VFP = 0000010)
  Frame frequency: 70 Hz
  Frequency fluctuation: 10%
  Internal oscillator clock (fosc.) [Hz] = 70 x [320+ 2 + 2] x 27 clocks x (1.1/0.9) ≒ 748KHz
  a-Si TFT LCD Single Chip Driver
  240RGBx320 Resolution and 262K color ILI9341
  The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
  reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
  Page 54 of 239
  When calculate the internal clock frequency, the oscillator variation is needed to be taken into consideration. In
  the above example, the calculated internal clock frequency with ±10% margin variation is considered and
  ensures to complete the display operation within one VSYNC cycle. The causes of frequency variation come
  from fabrication process of LSI, room temperature, external resistors and VCI voltage variation.
  Minimum speed for RAM writing [Hz] > 240 x 320 x 748K / [ (2 + 320 – 2)lines x 27clocks] ≒ 6.65 MHz
  The above theoretical value is calculated based on the premise that the ILI9341 starts to write data into the
  internal GRAM on the falling edge of VSYNC. There must at least be a margin of 2 lines between the physical
  display line and the GRAM line address where data writing operation is performed. The GRAM write speed of
  6.65MHz or more will guarantee the completion of GRAM write operation before the ILI9341 starts to display the
  GRAM data on the screen and enable to rewrite the entire screen without flicker.
  Notes in using the VSYNC interface

1. The minimum GRAM write speed must be satisfied and the frequency variation must be taken into
   consideration.
2. The display frame rate is determined by the VSYNC signal and the period of VSYNC must be longer than the
   scan period of an entire display.
3. When switching from the internal clock operation mode (DM[1:0] = “00”) to the VSYNC interface mode or
   inversely, the switching starts from the next VSYNC cycle, i.e. after completing the display of the frame.
4. The partial display, vertical scroll, and interlaced scan functions are not available in VSYNC interface mode.
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 55 of 239
   7.4. Color Depth Conversion Look Up Table
   When ILI9341 operates in parallel 16-bit interface, the color depth conversion is done by look-up table and
   extend input data format to 18-bit. See the detailed for look-up table of color depth conversion.
   R input (5-bit)
   16-bit/pixel –mode
   65,536 colors
   R output (6-bit)
   18-bit/pixel –mode
   262,144 colors
   Command Code (0x2Dh)
   RGBSET Parameter
   00000 R005 R004 R003 R002 R001 R000 1
   00001 R015 R014 R013 R012 R011 R010 2
   00010 R025 R024 R023 R022 R021 R020 3
   00011 R035 R034 R033 R032 R031 R030 4
   00100 R045 R044 R043 R042 R041 R040 5
   00101 R055 R054 R053 R052 R051 R050 6
   00110 R065 R064 R063 R062 R061 R060 7
   00111 R075 R074 R073 R072 R071 R070 8
   01000 R085 R084 R083 R082 R081 R080 9
   01001 R095 R094 R093 R092 R091 R090 10
   01010 R105 R104 R103 R102 R101 R100 11
   01011 R115 R114 R113 R112 R111 R110 12
   01100 R125 R124 R123 R122 R121 R120 13
   01101 R135 R134 R133 R132 R131 R130 14
   01110 R145 R144 R143 R142 R141 R140 15
   01111 R155 R154 R153 R152 R151 R150 16
   10000 R165 R164 R163 R162 R161 R160 17
   10001 R175 R174 R173 R172 R171 R170 18
   10010 R185 R184 R183 R182 R181 R180 19
   10011 R195 R194 R193 R192 R191 R190 20
   10100 R205 R204 R203 R202 R201 R200 21
   10101 R215 R214 R213 R212 R211 R210 22
   10110 R225 R224 R223 R222 R221 R220 23
   10111 R235 R234 R233 R232 R231 R230 24
   11000 R245 R244 R243 R242 R241 R240 25
   11001 R255 R254 R253 R252 R251 R250 26
   11010 R265 R264 R263 R262 R261 R260 27
   11011 R275 R274 R273 R272 R271 R270 28
   11100 R285 R284 R283 R282 R281 R280 29
   11101 R295 R294 R293 R292 R291 R290 30
   11110 R305 R304 R303 R302 R301 R300 31
   11111 R315 R314 R313 R312 R311 R310 32
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 56 of 239
   G input (6-bit)
   16-bit/pixel –mode
   65,536 colors
   G output (6-bit)
   18-bit/pixel –mode
   262,144 colors
   Command Code (0x2Dh)
   RGBSET Parameter
   000000 G005 G004 G003 G002 G001 G000 33
   000001 G015 G014 G013 G012 G011 G010 34
   000010 G025 G024 G023 G022 G021 G020 35
   000011 G035 G034 G033 G032 G031 G030 36
   000100 G045 G044 G043 G042 G041 G040 37
   000101 G055 G054 G053 G052 G051 G050 38
   000110 G065 G064 G063 G062 G061 G060 39
   000111 G075 G074 G073 G072 G071 G070 40
   001000 G085 G084 G083 G082 G081 G080 41
   001001 G095 G094 G093 G092 G091 G090 42
   001010 G105 G104 G103 G102 G101 G100 43
   001011 G115 G114 G113 G112 G111 G110 44
   001100 G125 G124 G123 G122 G121 G120 45
   001101 G135 G134 G133 G132 G131 G130 46
   001110 G145 G144 G143 G142 G141 G140 47
   001111 G155 G154 G153 G152 G151 G150 48
   010000 G165 G164 G163 G162 G161 G160 49
   010001 G175 G174 G173 G172 G171 G170 50
   010010 G185 G184 G183 G182 G181 G180 51
   010011 G195 G194 G193 G192 G191 G190 52
   010100 G205 G204 G203 G202 G201 G200 53
   010101 G215 G214 G213 G212 G211 G210 54
   010110 G225 G224 G223 G222 G221 G220 55
   010111 G235 G234 G233 G232 G231 G230 56
   011000 G245 G244 G243 G242 G241 G240 57
   011001 G255 G254 G253 G252 G251 G250 58
   011010 G265 G264 G263 G262 G261 G260 59
   011011 G275 G274 G273 G272 G271 G270 60
   011100 G285 G284 G283 G282 G281 G280 61
   011101 G295 G294 G293 G292 G291 G290 62
   011110 G305 G304 G303 G302 G301 G300 63
   011111 G315 G314 G313 G312 G311 G310 64
   100000 G325 G324 G323 G322 G321 G320 65
   100001 G335 G334 G333 G332 G331 G330 66
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 57 of 239
   G input (6-bit)
   16-bit/pixel –mode
   65,536 colors
   G output (6-bit)
   18-bit/pixel –mode
   262,144 colors
   Command Code (0x2Dh)
   RGBSET Parameter
   100010 G345 G344 G343 G342 G341 G340 67
   100011 G355 G354 G353 G352 G351 G350 68
   100100 G365 G364 G363 G362 G361 G360 69
   100101 G375 G374 G373 G372 G371 G370 70
   100110 G385 G384 G383 G382 G381 G380 71
   100111 G395 G394 G393 G392 G391 G390 72
   101000 G405 G404 G403 G402 G401 G400 73
   101001 G415 G414 G413 G412 G411 G410 74
   101010 G425 G424 G423 G422 G421 G420 75
   101011 G435 G434 G433 G432 G431 G430 76
   101100 G445 G444 G443 G442 G441 G440 77
   101101 G455 G454 G453 G452 G451 G450 78
   101110 G465 G464 G463 G462 G461 G460 79
   101111 G475 G474 G473 G472 G471 G470 80
   110000 G485 G484 G483 G482 G481 G480 81
   110001 G495 G494 G493 G492 G491 G490 82
   110010 G505 G504 G503 G502 G501 G500 83
   110011 G515 G514 G513 G512 G511 G510 84
   110100 G525 G524 G523 G522 G521 G520 85
   110101 G535 G534 G533 G532 G531 G530 86
   110110 G545 G544 G543 G542 G541 G540 87
   110111 G555 G554 G553 G552 G551 G550 88
   111000 G565 G564 G563 G562 G561 G560 89
   111001 G575 G574 G573 G572 G571 G570 90
   111010 G585 G584 G583 G582 G581 G580 91
   111011 G595 G594 G593 G592 G591 G590 92
   111100 G605 G604 G603 G602 G601 G600 93
   111101 G615 G614 G613 G612 G611 G610 94
   111110 G625 G624 G623 G622 G621 G620 95
   111111 G635 G634 G633 G632 G631 G630 96
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 58 of 239
   B input (5-bit)
   16-bit/pixel –mode
   65,536 colors
   B output (6-bit)
   18-bit/pixel –mode
   262,144 colors
   Command Code (0x2Dh)
   RGBSET Parameter
   00000 B005 B004 B003 B002 B001 B000 97
   00001 B015 B014 B013 B012 B011 B010 98
   00010 B025 B024 B023 B022 B021 B020 99
   00011 B035 B034 B033 B032 B031 B030 100
   00100 B045 B044 B043 B042 B041 B040 101
   00101 B055 B054 B053 B052 B051 B050 102
   00110 B065 B064 B063 B062 B061 B060 103
   00111 B075 B074 B073 B072 B071 B070 104
   01000 B085 B084 B083 B082 B081 B080 105
   01001 B095 B094 B093 B092 B091 B090 106
   01010 B105 B104 B103 B102 B101 B100 107
   01011 B115 B114 B113 B112 B111 B110 108
   01100 B125 B124 B123 B122 B121 B120 109
   01101 B135 B134 B133 B132 B131 B130 110
   01110 B145 B144 B143 B142 B141 B140 111
   01111 B155 B154 B153 B152 B151 B150 112
   10000 B165 B164 B163 B162 B161 B160 113
   10001 B175 B174 B173 B172 B171 B170 114
   10010 B185 B184 B183 B182 B181 B180 115
   10011 B195 B194 B193 B192 B191 B190 116
   10100 B205 B204 B203 B202 B201 B200 117
   10101 B215 B214 B213 B212 B211 B210 118
   10110 B225 B224 B223 B222 B221 B220 119
   10111 B235 B234 B233 B232 B231 B230 120
   11000 B245 B244 B243 B242 B241 B240 121
   11001 B255 B254 B253 B252 B251 B250 122
   11010 B265 B264 B263 B262 B261 B260 123
   11011 B275 B274 B273 B272 B271 B270 124
   11100 B285 B284 B283 B282 B281 B280 125
   11101 B295 B294 B293 B292 B291 B290 126
   11110 B305 B304 B303 B302 B301 B300 127
   11111 B315 B314 B313 B312 B311 B310 128
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 59 of 239
   7.5. Display Data RAM (DDRAM)
   ILI9341 has an integrated 240x320x18-bit graphic type static RAM. This 172,800-byte memory allows storing a
   240xRGBx320 image with an 18-bit resolution (262K-color). There is no abnormal visible effect on the display
   when there are simultaneous panel display read and interface read/write to the same location of the frame
   memory.
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 60 of 239
   7.6. Display Data Format
   ILI9341 supplies 18-/16-/9-/8-bit parallel MCU interface with 8080- / Ⅰ 8080- Ⅱ series, 3-/4-line serial interface
   and 6-/16-18-bit parallel RGB interface. The parallel MCU interface and serial interface mode can be selected by
   external pins IM [3:0] and RGB interface mode can be selected by software command parameters RCM[1:0].
   7.6.1. 3-line Serial Interface
   The 3-line/9-bit serial bus interface of ILI9341 can be used by setting external pin as IM [3:0] to “0101” for serial
   interface I or IM [3:0] to “1101” for serial interface II. The shown figure is the example of 3-line SPI interface.
   MPU Driver
   SCL
   CSX
   SDI
   SD0
   D[17:0]
   MPU Driver
   SCL
   CSX
   SDA
   D[17:0]
   3-line Serial Interface I
   3-line Serial Interface II
   In 3-line serial interface, different display data format is available for two color depths supported by the LCM
   listed below.
   -65k colors, RGB 5, 6, 5 -bits input
   -262k colors, RGB 6, 6, 6 -bits input.
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 61 of 239
   RESX
   IM[3:0] IM[3:0]=0101 or 1101
   CSX
   D8 D7 D6 D5 D4 D3 D2 D1 D0 D8 D7 D6 D5 D4 D3 D2 D1 D0 D8 D7 D6 D5 D4 D3 D2 D1 D0
   Pixel n Pixel n+1
   SDA
   SCL
   16-bit
   Frame memory
   1
   R1
   4
   R1
   3
   R1
   2
   R1
   1
   R1
   0
   G1
   5
   G1
   4
   G1
   3
   G1
   2
   G1
   1
   G1
   0
   B1
   4
   1
   B1
   3
   B1
   2
   B1
   1
   B1
   0
   R2
   4
   R2
   3
   R2
   2
   R2
   1
   R2
   0
   G2
   5
   G2
   4
   G2
   3
   1
   Look-Up Table for 65k Colors mapping (16-bit to 18-bit)
   18-bit
   R1 G1 B1 R2 G2 B2 R3 G3 B3
   16 bit/pixel color order (R:5-bit, G:6-bit, B:5-bit), 65,536 colors
   ‘1’
   Note 1: The pixel data with 16-bit color depth information.
   Note 2: The most significant bits are: Rx4, Gx5 and Bx4.
   Note 3: The least significant bits are: Rx0, Gx0 and Bx0.
   Note 4: ‘-‘= Don’t care –Can be set “0” or “1”.
   RESX
   ‘1’
   CSX
   D8 D7 D6 D5 D4 D3 D2 D1 D0 D8 D7 D6 D5 D4 D3 D2 D1 D0 D8 D7 D6 D5 D4 D3 D2 D1 D0
   Pixel n
   SDA
   SCL
   18-bit
   Frame memory
   1
   R1
   5
   R1
   4
   R1
   3
   R1
   2
   R1
   1
   R1
   0

- - G1
    5
    G1
    4
    G1
    3
    G1
    2
    1
    G1
    1
    G1
    0
- - B1
    5
    B1
    4
    B1
    3
    B1
    2
    B1
    1
    B1
    0
    1 - -
    R1 G1 B1 R2 G2 B2 R3 G3 B3
    18 bit/pixel color order (R:6-bit, G:6-bit, B:6-bit), 262,144 colors
    IM[3:0]=0101 or 1101 IM[3:0]
    Note 1: The pixel data with 18-bit color depth information.
    Note 2: The most significant bits are: Rx5, Gx5 and Bx5.
    Note 3: The least significant bits are : Rx0, Gx0 and Bx0.
    Note 4: ‘-‘= Don’t care - Can be set “0” or “1”.
    a-Si TFT LCD Single Chip Driver
    240RGBx320 Resolution and 262K color ILI9341
    The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
    reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
    Page 62 of 239
    RESX
    IM[3:0]
    CSX
- 0
  D23
  SCL
  High-Z R2Eh
  D22 D21 D20 D19 D18 D17 D16 D2 D1 D0 D23 D22 D21 D20 D19
  9 Dummy Clock
  SDA (I/F I) High-Z
  SDO (I/F II)
  1-Pixel data
  Read data through 3-line SPI mode
  ‘1’
  SDA (I/F I)
  SDI (I/F II)
  IM[3:0]=0101 or 1101
  Note 1: ‘-‘= Don’t care –Can be set “0” or “1”.
  a-Si TFT LCD Single Chip Driver
  240RGBx320 Resolution and 262K color ILI9341
  The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
  reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
  Page 63 of 239
  7.6.2. 4-line Serial Interface
  The 4-line/8-bit serial bus interface of ILI9341 can be used by setting external pin as IM [3:0] to “0110” for serial
  interface I or IM [3:0] to “1110” for serial interface II. The shown figure is the example of 4-line SPI interface.
  In 4-line serial interface, different display data format is available for two color depths supported by the LCM
  listed below.
  -65k colors, RGB 5, 6, 5 -bits input.
  -262k colors, RGB 6, 6, 6 -bits input.
  RESX
  IM[3:0] IM[3:0]=0110 or 1110
  CSX
  D7 D6 D5 D4 D3 D2 D1 D0 D7 D6 D5 D4 D3 D2 D1 D0 D7 D6 D5 D4 D3 D2 D1 D0
  Pixel n Pixel n+1
  SDA/
  SDI
  SCL
  16-bit
  Frame memory
  R1
  4
  R1
  3
  R1
  2
  R1
  1
  R1
  0
  G1
  5
  G1
  4
  G1
  3
  G1
  2
  G1
  1
  G1
  0
  B1
  4
  B1
  3
  B1
  2
  B1
  1
  B1
  0
  R2
  4
  R2
  3
  R2
  2
  R2
  1
  R2
  0
  G2
  5
  G2
  4
  G2
  3
  Look-Up Table for 65k Colors mapping (16-bit to 18-bit)
  18-bit
  R1 G1 B1 R2 G2 B2 R3 G3 B3
  16 bit/pixel color order (R:5-bit, G:6-bit, B:5-bit), 65,536 colors
  ‘1’
  D7 D6 D5
  G2
  2
  G2
  1
  G2
  0
  D/CX 1 1 1
  a-Si TFT LCD Single Chip Driver
  240RGBx320 Resolution and 262K color ILI9341
  The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
  reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
  Page 64 of 239
  Note 1: The pixel data with 16-bit color depth information.
  Note 2: The most significant bits are: Rx4, Gx5 and Bx4.
  Note 3: The least significant bits are: Rx0, Gx0 and Bx0.
  Note 4: ‘-‘= Don’t care –Can be set “0” or “1”.
  RESX
  CSX
  D7 D6 D5 D4 D3 D2 D1 D0 D7 D6 D5 D4 D3 D2 D1 D0 D7 D6 D5 D4 D3 D2 D1 D0
  Pixel n
  SCL
  Frame memory
  R1
  4
  R1
  3
  R1
  2
  R1
  1
  R1
  0
  G1
  5
  G1
  4
  G1
  3
  G1
  2
  G1
  0
  B1
  4
  B1
  3
  B1
  2
  B1
  1
  B1
  0
  18-bit
  R1 G1 B1 R2 G2 B2 R3 G3 B3
  D/CX 1 1
  G1
  1
  R1
  5
  B1
  5
  1
  ‘1’
  IM[3:0]=0110 or 1110 IM[3:0]
  SDA/
  SDI
  18 bit/pixel color order (R:6-bit, G:6-bit, B:6-bit), 262,144 colors
  Note 1: The pixel data with 18-bit color depth information.
  Note 2: The most significant bits are: Rx5, Gx5 and Bx5.
  Note 3: The least significant bits are: Rx0, Gx0 and Bx0.
  Note 4: ‘-‘= Don’t care –Can be set “0” or “1”.
  RESX'
  IM[3:0]
  CSX
- D23
  D23
  SCL
  R1
  3
  R1
  2
  R1
  1
  R1
  0
- - G1
    5
    G1
    4
    R2Eh
    D22 D21 D20 D19 D18 D17 D16 D2 D1 D0 D23 D22 D21 D20 D19
    8 Dummy Clock
    High-Z
    1-Pixel data
    Read Data format as below
    R1
    5
    R1
    4
    D22 D21 D20 D19 D18
    R1
    3
- - B1
    5
    R1
    3
    R1
    2
    D17 D16 D15 D14 D13 D12 D11 D10 D9 D8 D7 D6 D5 D4 D3 D2 D1 D0
- - R1
    1
    R1
    0
    B1
    4
    B1
    3
    B1
    2
    B1
    1
    B1
    0
    D/CX 0
    High-Z
    Driver
    Host
    Read data through 4-line SPI mode
    ‘1’
    IM[3:0]=0110 or 1110
    SDA (I/F I)
    SDO (I/F II)
    SDA (I/F I)
    SDI (I/F II)
    Note 1: ‘-‘= Don’t care – Can be set “0” or “1”.

a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 65 of 239
7.6.3. 8-bit Parallel MCU Interface
The 8080-Ⅰ system 8-bit parallel bus interface of ILI9341 can be used by setting external pin as IM [3:0] to
“0000”.The following shown figure is the example of interface with 8080-Ⅰ MCU system interface.
Different display data formats are available for two color depths supported by listed below.

- 65K-Colors, RGB 5, 6, 5 -bits input data.
- 262K-Colors, RGB 6, 6, 6 -bits input data.
  65K color: 16-bit/pixel (RGB 5-6-5 bits input)
  One pixel (3 sub-pixels) display data is sent by 2 byte transfers when DBI [2:0] bits of 3Ah register are set to
  “101”.
  Count 0 1 2 3 4 … 477 478 479 480
  D/CX 0 1 1 1 1 … 1 1 1 1
  D7 C7 0R4 0G2 1R4 1G2 … 238R4 238G2 239R4 239G2
  D6 C6 0R3 0G1 1R3 1G1 … 238R3 238G1 239R3 239G1
  D5 C5 0R2 0G0 1R2 1G0 … 238R2 238G0 239R2 239G0
  D4 C4 0R1 0B4 1R1 1B4 … 238R1 238B4 239R1 239B4
  D3 C3 0R0 0B3 1R0 1B3 … 238R0 238B3 239R0 239B3
  D2 C2 0G5 0B2 1G5 1B2 … 238G5 238B2 239G5 239B2
  D1 C1 0G4 0B1 1G4 1B1 … 238G4 238B1 239G4 239B1
  D0 C0 0G3 0B0 1G3 1B0 … 238G3 238B0 239G3 239B0
  262K color: 18-bit/pixel (RGB 6-6-6 bits input)
  One pixel (3 sub-pixels) display data is sent by 3 bytes transfer when DBI [2:0] bits of 3Ah register are set to
  “110”.
  Count 0 1 2 3 … 718 719 720
  D/CX 0 1 1 1 … 1 1 1
  D7 C7 0R5 0G5 0B5 … 239R5 239G5 239B5
  D6 C6 0R4 0G4 0B4 … 239R4 239G4 239B4
  D5 C5 0R3 0G3 0B3 … 239R3 239G3 239B3
  D4 C4 0R2 0G2 0B2 … 239R2 239G2 239B2
  D3 C3 0R1 0G1 0B1 … 239R1 239G1 239B1
  D2 C2 0R0 0G0 0B0 … 239R0 239G0 239B0
  D1 C1 …
  D0 C0 …
  a-Si TFT LCD Single Chip Driver
  240RGBx320 Resolution and 262K color ILI9341
  The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
  reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
  Page 66 of 239
  The 8080-Ⅱsystem 8-bit parallel bus interface of ILI9341 can be used by settings as IM [3:0] =”1001”. The
  following shown figure is the example of interface with 8080-Ⅱ MCU system interface.
  Different display data formats are available for two color depths supported by listed below.
- 65K-Colors, RGB 5, 6, 5 -bits input data.
- 262K-Colors, RGB 6, 6, 6 -bits input data.
  65K color: 16-bit/pixel (RGB 5-6-5 bits input)
  One pixel (3 sub-pixels) display data is sent by 2 byte transfers when DBI [2:0] bits of 3Ah register are set to
  “101”.
  Count 0 1 2 3 4 … 477 478 479 480
  D/CX 0 1 1 1 1 … 1 1 1 1
  D17 C7 0R4 0G2 1R4 1G2 … 238R4 238G2 239R4 239G2
  D16 C6 0R3 0G1 1R3 1G1 … 238R3 238G1 239R3 239G1
  D15 C5 0R2 0G0 1R2 1G0 … 238R2 238G0 239R2 239G0
  D14 C4 0R1 0B4 1R1 1B4 … 238R1 238B4 239R1 239B4
  D13 C3 0R0 0B3 1R0 1B3 … 238R0 238B3 239R0 239B3
  D12 C2 0G5 0B2 1G5 1B2 … 238G5 238B2 239G5 239B2
  D11 C1 0G4 0B1 1G4 1B1 … 238G4 238B1 239G4 239B1
  D10 C0 0G3 0B0 1G3 1B0 … 238G3 238B0 239G3 239B0
  262K color: 18-bit/pixel (RGB 6-6-6 bits input)
  One pixel (3 sub-pixels) display data is sent by 3 bytes transfer when DBI [2:0] bits of 3Ah register are set to
  “110”.
  Count 0 1 2 3 … 718 719 720
  D/CX 0 1 1 1 … 1 1 1
  D17 C7 0R5 0G5 0B5 … 239R5 239G5 239B5
  D16 C6 0R4 0G4 0B4 … 239R4 239G4 239B4
  D15 C5 0R3 0G3 0B3 … 239R3 239G3 239B3
  D14 C4 0R2 0G2 0B2 … 239R2 239G2 239B2
  D13 C3 0R1 0G1 0B1 … 239R1 239G1 239B1
  D12 C2 0R0 0G0 0B0 … 239R0 239G0 239B0
  D11 C1 …
  D10 C0 …
  a-Si TFT LCD Single Chip Driver
  240RGBx320 Resolution and 262K color ILI9341
  The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
  reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
  Page 67 of 239
  7.6.4. 9-bit Parallel MCU Interface
  The 8080-Ⅰ system 9-bit parallel bus interface of ILI9341 can be selected by setting hardware pin IM [3:0] to
  “0010”. The following shown figure is the example of interface with 8080-Ⅰ MCU system interface.
  65K color: 16-bit/pixel (RGB 5-6-5 bits input)
  One pixel (3 sub-pixels) display data is sent by 2 transfers when DBI [2:0] bits of 3Ah register are set to “101”.
  Count 0 1 2 3 4 … 477 478 479 480
  D/CX 0 1 1 1 1 … 1 1 1 1
  D8
  D7 C7 0R4 0G2 1R4 1G2 … 238R4 238G2 239R4 239G2
  D6 C6 0R3 0G1 1R3 1G1 … 238R3 238G1 239R3 239G1
  D5 C5 0R2 0G0 1R2 1G0 … 238R2 238G0 239R2 239G0
  D4 C4 0R1 0B4 1R1 1B4 … 238R1 238B4 239R1 239B4
  D3 C3 0R0 0B3 1R0 1B3 … 238R0 238B3 239R0 239B3
  D2 C2 0G5 0B2 1G5 1B2 … 238G5 238B2 239G5 239B2
  D1 C1 0G4 0B1 1G4 1B1 … 238G4 238B1 239G4 239B1
  D0 C0 0G3 0B0 1G3 1B0 … 238G3 238B0 239G3 239B0
  262K color: 18-bit/pixel (RGB 6-6-6 bits input)
  There are 2 pixels (6 sub-pixels) display data is sent by 4 transfers, when DBI [2:0] bits of 3Ah register are set to
  “110”.
  MDT[1:0]=”00”
  Count 0 1 2 3 4 … 478 478 479 480
  D/CX 0 1 1 1 1 … 1 1 1 1
  D8 0R5 0G2 1R5 1G2 238R5 238G2 239R5 239G2
  D7 C7 0R4 0G1 1R4 1G1 … 238R4 238G1 239R4 239G1
  D6 C6 0R3 0G0 1R3 1G0 … 238R3 238G0 239R3 239G0
  D5 C5 0R2 0B5 1R2 1B5 … 238R2 238B5 239R2 239B5
  D4 C4 0R1 0B4 1R1 1B4 … 238R1 238B4 239R1 239B4
  D3 C3 0R0 0B3 1R0 1B3 … 238R0 238B3 239R0 239B3
  D2 C2 0G5 0B2 1G5 1B2 … 238G5 238B2 239G5 239B2
  D1 C1 0G4 0B1 1G4 1B1 … 238G4 238B1 239G4 239B1
  D0 C0 0G3 0B0 1G3 1B0 … 238G3 238B0 239G3 239B0
  a-Si TFT LCD Single Chip Driver
  240RGBx320 Resolution and 262K color ILI9341
  The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
  reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
  Page 68 of 239
  MDT[1:0]=”01”
  Count 0 1 2 3 … 718 719 720
  D/CX 0 1 1 1 … 1 1 1
  D8
  D7 C7 0R5 0G5 0B5 … 239R5 239G5 239B5
  D6 C6 0R4 0G4 0B4 … 239R4 239G4 239B4
  D5 C5 0R3 0G3 0B3 … 239R3 239G3 239B3
  D4 C4 0R2 0G2 0B2 … 239R2 239G2 239B2
  D3 C3 0R1 0G1 0B1 … 239R1 239G1 239B1
  D2 C2 0R0 0G0 0B0 … 239R0 239G0 239B0
  D1 C1 …
  D0 C0 …
  The 8080- system 9 Ⅱ -bit parallel bus interface of ILI9341 can be selected by setting hardware pin IM [3:0] to
  “1011”. The following shown figure is the example of interface with 8080- MC Ⅱ U system interface.
  65K color: 16-bit/pixel (RGB 5-6-5 bits input)
  One pixel (3 sub-pixels) display data is sent by 2 transfers when DBI [2:0] bits of 3Ah register are set to “101”.
  Count 0 1 2 3 4 … 477 478 479 480
  D/CX 0 1 1 1 1 … 1 1 1 1
  D17 C7
  D16 C6 0R4 0G2 1R4 1G2 … 238R4 238G2 239R4 239G2
  D15 C5 0R3 0G1 1R3 1G1 … 238R3 238G1 239R3 239G1
  D14 C4 0R2 0G0 1R2 1G0 … 238R2 238G0 239R2 239G0
  D13 C3 0R1 0B4 1R1 1B4 … 238R1 238B4 239R1 239B4
  D12 C2 0R0 0B3 1R0 1B3 … 238R0 238B3 239R0 239B3
  D11 C1 0G5 0B2 1G5 1B2 … 238G5 238B2 239G5 239B2
  D10 C0 0G4 0B1 1G4 1B1 … 238G4 238B1 239G4 239B1
  D9 0G3 0B0 1G3 1B0 … 238G3 238B0 239G3 239B0
  a-Si TFT LCD Single Chip Driver
  240RGBx320 Resolution and 262K color ILI9341
  The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
  reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
  Page 69 of 239
  262K color: 18-bit/pixel (RGB 6-6-6 bits input)
  There are 2 pixels (6 sub-pixels) display data is sent by 4 transfers, when DBI [2:0] bits of 3Ah register are set to
  “110”.
  MDT[1:0]=”00”
  Count 0 1 2 3 4 … 478 478 479 480
  D/CX 0 1 1 1 1 … 1 1 1 1
  D17 C7 0R5 0G2 1R5 1G2 238R5 238G2 239R5 239G2
  D16 C6 0R4 0G1 1R4 1G1 … 238R4 238G1 239R4 239G1
  D15 C5 0R3 0G0 1R3 1G0 … 238R3 238G0 239R3 239G0
  D14 C4 0R2 0B5 1R2 1B5 … 238R2 238B5 239R2 239B5
  D13 C3 0R1 0B4 1R1 1B4 … 238R1 238B4 239R1 239B4
  D12 C2 0R0 0B3 1R0 1B3 … 238R0 238B3 239R0 239B3
  D11 C1 0G5 0B2 1G5 1B2 … 238G5 238B2 239G5 239B2
  D10 C0 0G4 0B1 1G4 1B1 … 238G4 238B1 239G4 239B1
  D9 0G3 0B0 1G3 1B0 … 238G3 238B0 239G3 239B0
  MDT[1:0]=”01”
  Count 0 1 2 3 … 718 719 720
  D/CX 0 1 1 1 … 1 1 1
  D17 C7
  D16 C6 0R5 0G5 0B5 … 239R5 239G5 239B5
  D15 C5 0R4 0G4 0B4 … 239R4 239G4 239B4
  D14 C4 0R3 0G3 0B3 … 239R3 239G3 239B3
  D13 C3 0R2 0G2 0B2 … 239R2 239G2 239B2
  D12 C2 0R1 0G1 0B1 … 239R1 239G1 239B1
  D11 C1 0R0 0G0 0B0 … 239R0 239G0 239B0
  D10 C0 …
  D9 …
  a-Si TFT LCD Single Chip Driver
  240RGBx320 Resolution and 262K color ILI9341
  The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
  reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
  Page 70 of 239
  7.6.5. 16-bit Parallel MCU Interface
  The 8080- Ⅰ system 16-bit parallel bus interface of ILI9341 can be selected by setting hardware pin IM[3:0] to
  “0001”.The following shown figure is the example of interface with 8080-Ⅰ MCU system interface.
  Different display data format is available for two colors depth supported by listed below.
- 65K-Colors, RGB 5, 6, 5 -bits input data.
- 262K-Colors, RGB 6, 6, 6 -bits input data.

65K color: 16-bit/pixel (RGB 5-6-5 bits input)
One pixel (3 sub-pixels) display data is sent by 1 transfer when DBI [2:0] bits of 3Ah register are set to “101”.
Count 0 1 2 3 … 238 239 240
D/CX 0 1 1 1 … 1 1 1
D15 0R4 1R4 2R4 … 237R4 238R4 239R4
D14 0R3 1R3 2R3 … 237R3 238R3 239R3
D13 0R2 1R2 2R2 … 237R2 238R2 239R2
D12 0R1 1R1 2R1 … 237R1 238R1 239R1
D11 0R0 1R0 2R0 … 237R0 238R0 239R0
D10 0G5 1G5 2G5 … 237G5 238G5 239G5
D9 0G4 1G4 2G4 … 237G4 238G4 239G4
D8 0G3 1G3 2G3 … 237G3 238G3 239G3
D7 C7 0G2 1G2 2G2 … 237G2 238G2 239G2
D6 C6 0G1 1G1 2G1 … 237G1 238G1 239G1
D5 C5 0G0 1G0 2G0 … 237G0 238G0 239G0
D4 C4 0B4 1B4 2B4 … 237B4 238B4 239B4
D3 C3 0B3 1B3 2B3 … 237B3 238B3 239B3
D2 C2 0B2 1B2 2B2 … 237B2 238B2 239B2
D1 C1 0B1 1B1 2B1 … 237B1 238B1 239B1
D0 C0 0B0 1B0 2B0 … 237B0 238B0 239B0
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 71 of 239
262K color: 18-bit/pixel (RGB 6-6-6 bits input)
One pixel (3 sub-pixels) display data is sent by 2 transfers when DBI [2:0] bits of 3Ah register are set to “110”.
MDT[1:0]=”00”
Count 0 1 2 3 … 358 359 360
D/CX 0 1 1 1 … 1 1 1
D15 0R5 0B5 1G5 … 238R5 238B5 239G5
D14 0R4 0B4 1G4 … 238R4 238B4 239G4
D13 0R3 0B3 1G3 … 238R3 238B3 239G3
D12 0R2 0B2 1G2 … 238R2 238B2 239G2
D11 0R1 0B1 1G1 … 238R1 238B1 239G1
D10 0R0 0B0 1G0 … 238R0 238B0 239G0
D9 …
D8 …
D7 C7 0G5 1R5 1B5 … 238G5 239R5 239B5
D6 C6 0G4 1R4 1B4 … 238G4 239R4 239B4
D5 C5 0G3 1R3 1B3 … 238G3 239R3 239B3
D4 C4 0G2 1R2 1B2 … 238G2 239R2 239B2
D3 C3 0G1 1R1 1B1 … 238G1 239R1 239B1
D2 C2 0G0 1R0 1B0 … 238G0 239R0 239B0
D1 C1 …
D0 C0 …
MDT[1:0]=”01”
Count 0 1 2 3 … 357 358 479 480
D/CX 0 1 1 1 … 1 1 1
D15 0R5 0B5 1R5 1B5 … 238R5 238B5 239R5 239B5
D14 0R4 0B4 1R4 1B4 … 238R4 238B4 239R4 239B4
D13 0R3 0B3 1R3 1B3 … 238R3 238B3 239R3 239B3
D12 0R2 0B2 1R2 1B2 … 238R2 238B2 239R2 239B2
D11 0R1 0B1 1R1 1B1 … 238R1 238B1 239R1 239B1
D10 0R0 0B0 1R0 1B0 … 238R0 238B0 239R0 239B0
D9 …
D8 …
D7 C7 0G5 1G5 … 238G5 239G5
D6 C6 0G4 1G4 … 238G4 239G4
D5 C5 0G3 1G3 … 238G3 239G3
D4 C4 0G2 1G2 … 238G2 239G2
D3 C3 0G1 1G1 … 238G1 239G1
D2 C2 0G0 1G0 … 238G0 239G0
D1 C1 …
D0 C0 …
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 72 of 239
MDT[1:0]=”10”
Count 0 1 2 3 … 357 358 479 480
D/CX 0 1 1 1 … 1 1 1
D15 0R5 0B1 1R5 1B1 … 238R5 238B1 239R5 239B1
D14 0R4 0B0 1R4 1B0 … 238R4 238B0 239R4 239B0
D13 0R3 1R3 … 238R3 239R3
D12 0R2 1R2 … 238R2 239R2
D11 0R1 1R1 … 238R1 239R1
D10 0R0 1R0 … 238R0 239R0
D9 0G5 1G5 … 238G5 239G5
D8 0G4 1G4 … 238G4 239G4
D7 C7 0G3 1G3 … 238G3 239G3
D6 C6 0G2 1G2 … 238G2 239G2
D5 C5 0G1 1G1 … 238G1 239G1
D4 C4 0G0 1G0 … 238G0 239G0
D3 C3 0B5 1B5 … 238B5 239B5
D2 C2 0B4 1B4 … 238B4 239B4
D1 C1 0B3 1B3 … 238B3 239B3
D0 C0 0B2 1B2 … 238B2 239B2
MDT[1:0]=”11”
Count 0 1 2 3 … 357 358 479 480
D/CX 0 1 1 1 … 1 1 1
D15 0R3 1R3 … 238R3 239R3
D14 0R2 1R2 … 238R2 239R2
D13 0R1 1R1 … 238R1 239R1
D12 0R0 1R0 … 238R0 239R0
D11 0G5 1G5 … 238G5 239G5
D10 0G4 1G4 … 238G4 239G4
D9 0G3 1G3 … 238G3 239G3
D8 0G2 1G2 … 238G2 239G2
D7 C7 0G1 1G1 … 238G1 239G1
D6 C6 0G0 1G0 … 238G0 239G0
D5 C5 0B5 1B5 … 238B5 239B5
D4 C4 0B4 1B4 … 238B4 239B4
D3 C3 0B3 1B3 … 238B3 239B3
D2 C2 0B2 1B2 … 238B2 239B2
D1 C1 0R5 0B1 1R5 1B1 … 238R5 238B1 239R5 239B1
D0 C0 0R4 0B0 1R4 1B0 … 238R4 238B0 239R4 239B0
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 73 of 239
The 8080- system 16 Ⅱ -bit parallel bus interface of ILI9341 can be selected by settings IM [3:0] =”1000”. The
following shown figure is the example of interface with 8080- MCU system interface. Ⅱ
Different display data format is available for two colors depth supported by listed below.

- 65K-Colors, RGB 5, 6, 5 -bits input data.
- 262K-Colors, RGB 6, 6, 6 -bits input data.

65K color: 16-bit/pixel (RGB 5-6-5 bits input)
One pixel (3 sub-pixels) display data is sent by 1 transfer when DBI [2:0] bits of 3Ah register are set to “101”.
Count 0 1 2 3 … 238 239 240
D/CX 0 1 1 1 … 1 1 1
D17 0R4 1R4 2R4 … 237R4 238R4 239R4
D16 0R3 1R3 2R3 … 237R3 238R3 239R3
D15 0R2 1R2 2R2 … 237R2 238R2 239R2
D14 0R1 1R1 2R1 … 237R1 238R1 239R1
D13 0R0 1R0 2R0 … 237R0 238R0 239R0
D12 0G5 1G5 2G5 … 237G5 238G5 239G5
D11 0G4 1G4 2G4 … 237G4 238G4 239G4
D10 0G3 1G3 2G3 … 237G3 238G3 239G3
D8 C7 0G2 1G2 2G2 … 237G2 238G2 239G2
D7 C6 0G1 1G1 2G1 … 237G1 238G1 239G1
D6 C5 0G0 1G0 2G0 … 237G0 238G0 239G0
D5 C4 0B4 1B4 2B4 … 237B4 238B4 239B4
D4 C3 0B3 1B3 2B3 … 237B3 238B3 239B3
D3 C2 0B2 1B2 2B2 … 237B2 238B2 239B2
D2 C1 0B1 1B1 2B1 … 237B1 238B1 239B1
D1 C0 0B0 1B0 2B0 … 237B0 238B0 239B0
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 74 of 239
262K color: 18-bit/pixel (RGB 6-6-6 bits input)
One pixel (3 sub-pixels) display data is sent by 2 transfers when DBI [2:0] bits of 3Ah register are set to “110”.
MDT[1:0]=”00”
Count 0 1 2 3 … 358 359 360
D/CX 0 1 1 1 … 1 1 1
D17 0R5 0B5 1G5 … 238R5 238B5 239G5
D16 0R4 0B4 1G4 … 238R4 238B4 239G4
D15 0R3 0B3 1G3 … 238R3 238B3 239G3
D14 0R2 0B2 1G2 … 238R2 238B2 239G2
D13 0R1 0B1 1G1 … 238R1 238B1 239G1
D12 0R0 0B0 1G0 … 238R0 238B0 239G0
D11 …
D10 …
D8 C7 0G5 1R5 1B5 … 238G5 239R5 239B5
D7 C6 0G4 1R4 1B4 … 238G4 239R4 239B4
D6 C5 0G3 1R3 1B3 … 238G3 239R3 239B3
D5 C4 0G2 1R2 1B2 … 238G2 239R2 239B2
D4 C3 0G1 1R1 1B1 … 238G1 239R1 239B1
D3 C2 0G0 1R0 1B0 … 238G0 239R0 239B0
D2 C1 …
D1 C0 …
MDT[1:0]=”01”
Count 0 1 2 3 … 357 358 479 480
D/CX 0 1 1 1 … 1 1 1
D17 0R5 0B5 1R5 1B5 … 238R5 238B5 239R5 239B5
D16 0R4 0B4 1R4 1B4 … 238R4 238B4 239R4 239B4
D15 0R3 0B3 1R3 1B3 … 238R3 238B3 239R3 239B3
D14 0R2 0B2 1R2 1B2 … 238R2 238B2 239R2 239B2
D13 0R1 0B1 1R1 1B1 … 238R1 238B1 239R1 239B1
D12 0R0 0B0 1R0 1B0 … 238R0 238B0 239R0 239B0
D11 …
D10 …
D8 C7 0G5 1G5 … 238G5 239G5
D7 C6 0G4 1G4 … 238G4 239G4
D6 C5 0G3 1G3 … 238G3 239G3
D5 C4 0G2 1G2 … 238G2 239G2
D4 C3 0G1 1G1 … 238G1 239G1
D3 C2 0G0 1G0 … 238G0 239G0
D2 C1 …
D1 C0 …
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 75 of 239
MDT[1:0]=”10”
Count 0 1 2 3 … 357 358 479 480
D/CX 0 1 1 1 … 1 1 1
D17 0R5 0B1 1R5 1B1 … 238R5 238B1 239R5 239B1
D16 0R4 0B0 1R4 1B0 … 238R4 238B0 239R4 239B0
D15 0R3 1R3 … 238R3 239R3
D14 0R2 1R2 … 238R2 239R2
D13 0R1 1R1 … 238R1 239R1
D12 0R0 1R0 … 238R0 239R0
D11 0G5 1G5 … 238G5 239G5
D10 0G4 1G4 … 238G4 239G4
D8 C7 0G3 1G3 … 238G3 239G3
D7 C6 0G2 1G2 … 238G2 239G2
D6 C5 0G1 1G1 … 238G1 239G1
D5 C4 0G0 1G0 … 238G0 239G0
D4 C3 0B5 1B5 … 238B5 239B5
D3 C2 0B4 1B4 … 238B4 239B4
D2 C1 0B3 1B3 … 238B3 239B3
D1 C0 0B2 1B2 … 238B2 239B2
MDT[1:0]=”11”
Count 0 1 2 3 … 357 358 479 480
D/CX 0 1 1 1 … 1 1 1
D17 0R3 1R3 … 238R3 239R3
D16 0R2 1R2 … 238R2 239R2
D15 0R1 1R1 … 238R1 239R1
D14 0R0 1R0 … 238R0 239R0
D13 0G5 1G5 … 238G5 239G5
D12 0G4 1G4 … 238G4 239G4
D11 0G3 1G3 … 238G3 239G3
D10 0G2 1G2 … 238G2 239G2
D8 C7 0G1 1G1 … 238G1 239G1
D7 C6 0G0 1G0 … 238G0 239G0
D6 C5 0B5 1B5 … 238B5 239B5
D5 C4 0B4 1B4 … 238B4 239B4
D4 C3 0B3 1B3 … 238B3 239B3
D3 C2 0B2 1B2 … 238B2 239B2
D2 C1 0R5 0B1 1R5 1B1 … 238R5 238B1 239R5 239B1
D1 C0 0R4 0B0 1R4 1B0 … 238R4 238B0 239R4 239B0
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 76 of 239
7.6.6. 18-bit Parallel MCU Interface
The 8080- Ⅰ system 18-bit parallel bus interface of ILI9341 can be selected by setting hardware pin IM[3:0] to
“0011”.The following shown figure is the example of interface with 8080-Ⅰ MCU system interface.
Different display data format is available for one color depth only supported by listed below.

- 65K-Colors, RGB 5, 6, 5 -bits input data.
- 262K-Colors, RGB 6, 6, 6 -bits input data.
  65K color: 16-bit/pixel (RGB 5-6-5 bits input)
  One pixel (3 sub-pixels) display data is sent by 1 transfer when DBI [2:0] bits of 3Ah register are set to “101”.
  Count 0 1 2 3 … 238 239 240
  D/CX 0 1 1 1 … 1 1 1
  D17
  D16
  D15 0R4 1R4 2R4 … 237R4 238R4 239R4
  D14 0R3 1R3 2R3 … 237R3 238R3 239R3
  D13 0R2 1R2 2R2 … 237R2 238R2 239R2
  D12 0R1 1R1 2R1 … 237R1 238R1 239R1
  D11 0R0 1R0 2R0 … 237R0 238R0 239R0
  D10 0G5 1G5 2G5 … 237G5 238G5 239G5
  D9 0G4 1G4 2G4 … 237G4 238G4 239G4
  D8 0G3 1G3 2G3 … 237G3 238G3 239G3
  D7 C7 0G2 1G2 2G2 … 237G2 238G2 239G2
  D6 C6 0G1 1G1 2G1 … 237G1 238G1 239G1
  D5 C5 0G0 1G0 2G0 … 237G0 238G0 239G0
  D4 C4 0B4 1B4 2B4 … 237B4 238B4 239B4
  D3 C3 0B3 1B3 2B3 … 237B3 238B3 239B3
  D2 C2 0B2 1B2 2B2 … 237B2 238B2 239B2
  D1 C1 0B1 1B1 2B1 … 237B1 238B1 239B1
  D0 C0 0B0 1B0 2B0 … 237B0 238B0 239B0
  a-Si TFT LCD Single Chip Driver
  240RGBx320 Resolution and 262K color ILI9341
  The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
  reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
  Page 77 of 239
  262K color: 18-bit/pixel (RGB 6-6-6 bits input)
  One pixel (3 sub-pixels) display data is sent by 1 transfer when DBI [2:0] bits of 3Ah register are set to “110”.
  Count 0 1 2 3 … 238 239 240
  D/CX 0 1 1 1 … 1 1 1
  D17 0R5 1R5 2R5 … 237R5 238R5 239R5
  D16 0R4 1R4 2R4 … 237R4 238R4 239R4
  D15 0R3 1R3 2R3 … 237R3 238R3 239R3
  D14 0R2 1R2 2R2 … 237R2 238R2 239R2
  D13 0R1 1R1 2R1 … 237R1 238R1 239R1
  D12 0R0 1R0 2R0 … 237R0 238R0 239R0
  D11 0G5 1G5 2G5 … 237G5 238G5 239G5
  D10 0G4 1G4 2G4 … 237G4 238G4 239G4
  D9 0G3 1G3 2G3 … 237G3 238G3 239G3
  D8 0G2 1G2 2G2 … 237G2 238G2 239G2
  D7 C7 0G1 1G1 2G1 … 237G1 238G1 239G1
  D6 C6 0G0 1G0 2G0 … 237G0 238G0 239G0
  D5 C5 0B5 1B5 2B5 … 237B5 238B5 239B5
  D4 C4 0B4 1B4 2B4 … 237B4 238B4 239B4
  D3 C3 0B3 1B3 2B3 … 237B3 238B3 239B3
  D2 C2 0B2 1B2 2B2 … 237B2 238B2 239B2
  D1 C1 0B1 1B1 2B1 … 237B1 238B1 239B1
  D0 C0 0B0 1B0 2B0 … 237B0 238B0 239B0
  a-Si TFT LCD Single Chip Driver
  240RGBx320 Resolution and 262K color ILI9341
  The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
  reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
  Page 78 of 239
  The 8080- system 18 Ⅱ -bit parallel bus interface mode can be selected by settings IM [3:0] =”1010”. The
  following shown figure is the example of interface with 8080- MCU system interface. Ⅱ
  Different display data format is available for one color depth only supported by listed below.
- 65K-Colors, RGB 5, 6, 5 -bits input data.
- 262K-Colors, RGB 6, 6, 6 -bits input data.
  65K color: 16-bit/pixel (RGB 5-6-5 bits input)
  One pixel (3 sub-pixels) display data is sent by 1 transfer when DBI [2:0] bits of 3Ah register are set to “101”.
  Count 0 1 2 3 … 238 239 240
  D/CX 0 1 1 1 … 1 1 1
  D17
  D16
  D15 0R4 1R4 2R4 … 237R4 238R4 239R4
  D14 0R3 1R3 2R3 … 237R3 238R3 239R3
  D13 0R2 1R2 2R2 … 237R2 238R2 239R2
  D12 0R1 1R1 2R1 … 237R1 238R1 239R1
  D11 0R0 1R0 2R0 … 237R0 238R0 239R0
  D10 0G5 1G5 2G5 … 237G5 238G5 239G5
  D9 0G4 1G4 2G4 … 237G4 238G4 239G4
  D8 C7 0G3 1G3 2G3 … 237G3 238G3 239G3
  D7 C6 0G2 1G2 2G2 … 237G2 238G2 239G2
  D6 C5 0G1 1G1 2G1 … 237G1 238G1 239G1
  D5 C4 0G0 1G0 2G0 … 237G0 238G0 239G0
  D4 C3 0B4 1B4 2B4 … 237B4 238B4 239B4
  D3 C2 0B3 1B3 2B3 … 237B3 238B3 239B3
  D2 C1 0B2 1B2 2B2 … 237B2 238B2 239B2
  D1 C0 0B1 1B1 2B1 … 237B1 238B1 239B1
  D0 0B0 1B0 2B0 … 237B0 238B0 239B0
  a-Si TFT LCD Single Chip Driver
  240RGBx320 Resolution and 262K color ILI9341
  The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
  reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
  Page 79 of 239
  262K color: 18-bit/pixel (RGB 6-6-6 bits input)
  One pixel (3 sub-pixels) display data is sent by 1 transfer when DBI [2:0] bits of 3Ah register are set to “110”.
  Count 0 1 2 3 … 238 239 240
  D/CX 0 1 1 1 … 1 1 1
  D17 0R5 1R5 2R5 … 237R5 238R5 239R5
  D16 0R4 1R4 2R4 … 237R4 238R4 239R4
  D15 0R3 1R3 2R3 … 237R3 238R3 239R3
  D14 0R2 1R2 2R2 … 237R2 238R2 239R2
  D13 0R1 1R1 2R1 … 237R1 238R1 239R1
  D12 0R0 1R0 2R0 … 237R0 238R0 239R0
  D11 0G5 1G5 2G5 … 237G5 238G5 239G5
  D10 0G4 1G4 2G4 … 237G4 238G4 239G4
  D9 0G3 1G3 2G3 … 237G3 238G3 239G3
  D8 C7 0G2 1G2 2G2 … 237G2 238G2 239G2
  D7 C6 0G1 1G1 2G1 … 237G1 238G1 239G1
  D6 C5 0G0 1G0 2G0 … 237G0 238G0 239G0
  D5 C4 0B5 1B5 2B5 … 237B5 238B5 239B5
  D4 C3 0B4 1B4 2B4 … 237B4 238B4 239B4
  D3 C2 0B3 1B3 2B3 … 237B3 238B3 239B3
  D2 C1 0B2 1B2 2B2 … 237B2 238B2 239B2
  D1 C0 0B1 1B1 2B1 … 237B1 238B1 239B1
  D0 0B0 1B0 2B0 … 237B0 238B0 239B0
  a-Si TFT LCD Single Chip Driver
  240RGBx320 Resolution and 262K color ILI9341
  The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
  reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
  Page 80 of 239
  7.6.7. 6-bit Parallel RGB Interface
  The 6-bit RGB interface is selected by setting the DPI [2:0] bit to “110”. When RCM [1:0] are set to “10” and DE
  mode is selected, the display operation is synchronized with VSYNC, HSYNC and DOTCLK signals. The
  display data are transferred to the internal GRAM in synchronization with the display operation via 6-bit RGB
  data bus (D [5:0]) according to the data enable signal (DE) when RCM [1:0] are set to “10”. The RGB interface
  SYNC mode is selected by setting the RCM [1:0] to “11”, the valid display data is inputted in pixel unit via D [5:0]
  according to the VFP/VBP and HFP/HBP settings. Unused pins must be connected to GND to ensure normally
  operation. Registers can be set by the SPI system interface.
  65K color: 16-bit/pixel (RGB 5-6-5 bits input)
  262K color: 18-bit/pixel (RGB 6-6-6 bits input)
  ILI9341 has data transfer counters to count the first, second, third data transfer in 6-bit RGB interface mode. The
  transfer counter is always reset to the state of first data transfer on the falling edge of VSYNC. If a mismatch
  arises in the number of each data transfer, the counter is reset to the state of first data transfer at the start of the
  frame (i.e. on the falling edge of VSYNC) to restart data transfer in the correct order from the next frame. This
  function is expedient for moving picture display, which requires consecutive data transfer in light of minimizing
  effects from failed data transfer and enabling the system to return to a normal state.
  Note that internal display operation is performed in units of pixels (RGB: taking 3 inputs of DOTCLK).
  Accordingly, the number of DOTCLK inputs in one frame period must be a multiple of 3 to complete data transfer
  correctly. Otherwise it will affect the display of that frame as well as the next frame.
  a-Si TFT LCD Single Chip Driver
  240RGBx320 Resolution and 262K color ILI9341
  The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
  reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
  Page 81 of 239
  HSYNC
  DOTCLK
  ENABLE
  VSYNC
  HSYNC
  ENABLE
  VBP Active Area VFP
  Totale Area
  HBP Active Area HFP
  Totale Area
  D[5:0]
  DE Mode, RCM[1:0]=“10”
  a-Si TFT LCD Single Chip Driver
  240RGBx320 Resolution and 262K color ILI9341
  The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
  reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
  Page 82 of 239
  7.6.8. 16-bit Parallel RGB Interface
  The 16-bit RGB interface is selected by setting the DPI [2:0] bits to “101”. When RCM [1:0] are set to “10” and
  DE mode is selected, the display operation is synchronized with VSYNC, HSYNC and DOTCLK signals. The
  display data is transferred to the internal GRAM in synchronization with the display operation via 16-bit RGB
  data bus (D [17:13] & D [11:1]) according to the data enable signal (DE). The RGB interface SYNC mode is
  selected by setting the RCM [1:0] to “11”, the valid display data is inputted in pixel unit via D [17:13] and D [11:1]
  according to the VFP/VBP and HFP/HBP settings. The unused D12 and D0 pins must be connected to GND for
  ensure normally operation. Registers can be set by the SPI system interface.
  R5 R4 R3 R2 R1 R0 G5 G4 G3 G2 G1 G0 B5 B4 B3 B2 B1 B0
  D17 D16 D15 D14 D13 D11 D10 D9 D8 D7 D6 D5 D4 D3 D2 D1
  D17 D16 D15 D14 D13 D11 D10 D9 D8 D7 D6 D5 D4 D3 D2 D1 Input
  Data
  Write Data
  Register
  GRAM Data &
  RGB Mapping
  Look-Up Table for 65k Colors mapping (16-bit to 18-bit)
  7.6.9. 18-bit Parallel RGB Interface
  The 18-bit RGB interface is selected by setting the DPI [2:0] bits to “110”. When RCM [1:0] are set to “10” and
  DE mode is selected, the display operation is synchronized with VSYNC, HSYNC and DOTCLK signals. The
  display data are transferred to the internal GRAM in synchronization with the display operation via 18-bit RGB
  data bus (D [17:0]) according to the data enable signal (DE) when RCM [1:0] are set to “10”. The RGB interface
  SYNC mode is selected by setting the RCM [1:0] to “11”, the valid display data is inputted in pixel unit via D [17:0]
  according to the VFP/VBP and HFP/HBP settings. Registers can be set by the SPI system interface.
  a-Si TFT LCD Single Chip Driver
  240RGBx320 Resolution and 262K color ILI9341
  The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
  reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
  Page 83 of 239

8. Command
   8.1. Command List
   Regulative Command Set
   Command Function D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 Hex
   No Operation 0 1 ↑ XX 0 0 0 0 0 0 0 0 00h
   Software Reset 0 1 ↑ XX 0 0 0 0 0 0 0 1 01h
   0 1 ↑ XX 0 0 0 0 0 1 0 0 04h
   1 ↑ 1 XX X X X X X X X X XX
   1 ↑ 1 XX ID1 [7:0] XX
   1 ↑ 1 XX ID2 [7:0] XX
   Read Display Identification
   Information
   1 ↑ 1 XX ID3 [7:0] XX
   0 1 ↑ XX 0 0 0 0 1 0 0 1 09h
   1 ↑ 1 XX X X X X X X X X XX
   1 ↑ 1 XX D [31:25] X 00
   1 ↑ 1 XX X D [22:20] D [19:16] 61
   1 ↑ 1 XX X X X X X D [10:8] 00
   Read Display Status
   1 ↑ 1 XX D [7:5] X X X X X 00
   0 1 ↑ XX 0 0 0 0 1 0 1 0 0Ah
   Read Display Power Mode 1 ↑ 1 XX X X X X X X X X XX
   1 ↑ 1 XX D [7:2] 0 0 08
   0 1 ↑ XX 0 0 0 0 1 0 1 1 0Bh
   Read Display MADCTL 1 ↑ 1 XX X X X X X X X X XX
   1 ↑ 1 XX D [7:2] 0 0 00
   0 1 ↑ XX 0 0 0 0 1 1 0 0 0Ch
   Read Display Pixel Format 1 ↑ 1 XX X X X X X X X X XX
   1 ↑ 1 XX RIM DPI [2:0] X DBI [2:0] 06
   0 1 ↑ XX 0 0 0 0 1 1 0 1 0Dh
   Read Display Image Format 1 ↑ 1 XX X X X X X X X X XX
   1 ↑ 1 XX X X X X X D [2:0] 00
   0 1 ↑ XX 0 0 0 0 1 1 1 0 0Eh
   Read Display Signal Mode 1 ↑ 1 XX X X X X X X X X XX
   1 ↑ 1 XX D [7:2] 0 0 00
   0 1 ↑ XX 0 0 0 0 1 1 1 1 0Fh
   1 ↑ 1 XX X X X X X X X X XX
   Read Display Self-Diagnostic
   Result
   1 ↑ 1 XX D [7:6] X X X X X X 00
   Enter Sleep Mode 0 1 ↑ XX 0 0 0 1 0 0 0 0 10h
   Sleep OUT 0 1 ↑ XX 0 0 0 1 0 0 0 1 11h
   Partial Mode ON 0 1 ↑ XX 0 0 0 1 0 0 1 0 12h
   Normal Display Mode ON 0 1 ↑ XX 0 0 0 1 0 0 1 1 13h
   Display Inversion OFF 0 1 ↑ XX 0 0 1 0 0 0 0 0 20h
   Display Inversion ON 0 1 ↑ XX 0 0 1 0 0 0 0 1 21h
   0 1 ↑ XX 0 0 1 0 0 1 1 0 26h
   Gamma Set
   1 1 ↑ XX GC [7:0] 01
   Display OFF 0 1 ↑ XX 0 0 1 0 1 0 0 0 28h
   Display ON 0 1 ↑ XX 0 0 1 0 1 0 0 1 29h
   0 1 ↑ XX 0 0 1 0 1 0 1 0 2Ah
   1 1 ↑ XX SC [15:8] XX
   1 1 ↑ XX SC [7:0] XX
   1 1 ↑ XX EC [15:8] XX
   Column Address Set
   1 1 ↑ XX EC [7:0] XX
   0 1 ↑ XX 0 0 1 0 1 0 1 1 2Bh
   1 1 ↑ XX SP [15:8] XX
   1 1 ↑ XX SP [7:0] XX
   1 1 ↑ XX EP [15:8] XX
   Page Address Set
   1 1 ↑ XX EP [7:0] XX
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 84 of 239
   0 1 ↑ XX 0 0 1 0 1 1 0 0 2Ch
   Memory Write
   1 1 ↑ D [17:0] XX
   0 1 ↑ XX 0 0 1 0 1 1 0 1 2Dh
   1 ↑ 1 XX R00 [5:0] XX
   1 ↑ 1 XX Rnn [5:0] XX
   1 ↑ 1 XX R31 [5:0] XX
   1 ↑ 1 XX G00 [5:0] XX
   1 ↑ 1 XX Gnn [5:0] XX
   1 ↑ 1 XX G64 [5:0] XX
   1 ↑ 1 XX B00 [5:0] XX
   1 ↑ 1 XX Bnn [5:0] XX
   Color SET
   1 ↑ 1 XX B31 [5:0] XX
   0 1 ↑ XX 0 0 1 0 1 1 1 0 2Eh
   Memory Read 1 ↑ 1 XX X X X X X X X X XX
   1 ↑ 1 D [17:0] XX
   0 1 ↑ XX 0 0 1 1 0 0 0 0 30h
   1 1 ↑ XX SR [15:8] 00
   1 1 ↑ XX SR [7:0] 00
   1 1 ↑ XX ER [15:8] 01
   Partial Area
   1 1 ↑ XX ER [7:0] 3F
   0 1 ↑ XX 0 0 1 1 0 0 1 1 33h
   1 1 ↑ XX TFA [15:8] 00
   1 1 ↑ XX TFA [7:0] 00
   1 1 ↑ XX VSA [15:8] 01
   1 1 ↑ XX VSA [7:0] 40
   1 1 ↑ XX BFA [15:8] 00
   Vertical Scrolling Definition
   1 1 ↑ XX BFA [7:0] 00
   Tearing Effect Line OFF 0 1 ↑ XX 0 0 1 1 0 1 0 0 34h
   0 1 ↑ XX 0 0 1 1 0 1 0 1 35h
   Tearing Effect Line ON
   1 1 ↑ XX X X X X X X X M 00
   0 1 ↑ XX 0 0 1 1 0 1 1 0 36h
   Memory Access Control
   1 1 ↑ XX MY MX MV ML BGR MH X X 00
   0 1 ↑ XX 0 0 1 1 0 1 1 1 37h
   Vertical Scrolling Start Address 1 1 ↑ XX VSP [15:8] 00
   1 1 ↑ XX VSP [7:0] 00
   Idle Mode OFF 0 1 ↑ XX 0 0 1 1 1 0 0 0 38h
   Idle Mode ON 0 1 ↑ XX 0 0 1 1 1 0 0 1 39h
   0 1 ↑ XX 0 0 1 1 1 0 1 0 3Ah
   Pixel Format Set
   1 1 ↑ XX X DPI [2:0] X DBI [2:0] 66
   0 1 ↑ XX 0 0 1 1 1 1 0 0 3Ch
   Write Memory Continue
   1 1 ↑ D [17:0] XX
   0 1 ↑ XX 0 0 1 1 1 1 1 0 3Eh
   Read Memory Continue 1 ↑ 1 XX X X X X X X X X XX
   1 ↑ 1 D [17:0] XX
   0 1 ↑ XX 0 1 0 0 0 1 0 0 44h
   Set Tear Scanline 1 1 ↑ XX X X X X X X X STS [8] 00
   1 1 ↑ XX STS [7:0] 00
   0 1 ↑ XX 0 1 0 0 0 1 0 1 45h
   1 ↑ 1 XX X X X X X X X X XX
   1 ↑ 1 XX X X X X X X GTS [9:8] 00
   Get Scanline
   1 ↑ 1 XX GTS [7:0] 00
   0 1 ↑ XX 0 1 0 1 0 0 0 1 51h
   Write Display Brightness
   1 1 ↑ XX DBV [7:0] 00
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 85 of 239
   0 1 ↑ XX 0 1 0 1 0 0 1 0 52h
   Read Display Brightness 1 ↑ 1 XX X X X X X X X X XX
   1 ↑ 1 XX DBV [7:0] 00
   0 1 ↑ XX 0 1 0 1 0 0 1 1 53h Write CTRL Display
   1 1 ↑ XX X X BCTRL X DD BL X X 00
   0 1 ↑ XX 0 1 0 1 0 1 0 0 54h
   Read CTRL Display 1 ↑ 1 XX X X X X X X X X XX
   1 ↑ 1 XX X X BCTRL X DD BL X X 00
   Write Content Adaptive 0 1 ↑ XX 0 1 0 1 0 1 0 1 55h
   Brightness Control 1 1 ↑ XX X X X X X X C [1:0] 00
   0 1 ↑ XX 0 1 0 1 0 1 1 0 56h
   1 ↑ 1 XX X X X X X X X X XX Read Content Adaptive
   Brightness Control
   1 ↑ 1 XX X X X X X X C [1:0] 00
   Write CABC Minimum 0 1 ↑ XX 0 1 0 1 1 1 1 0 5Eh
   Brightness 1 1 ↑ XX CMB [7:0] 00
   0 1 ↑ XX 0 1 0 1 0 1 1 1 5Fh
   1 ↑ 1 XX X X X X X X X X XX Read CABC Minimum
   Brightness
   1 ↑ 1 XX CMB [7:0] 00
   0 1 ↑ XX 1 1 0 1 1 0 1 0 DAh
   Read ID1 1 ↑ 1 XX X X X X X X X X XX
   1 ↑ 1 XX Module’s Manufacture [7:0] XX
   0 1 ↑ XX 1 1 0 1 1 0 1 1 DBh
   Read ID2 1 ↑ 1 XX X X X X X X X X XX
   1 ↑ 1 XX LCD Module / Driver Version [7:0] XX
   0 1 ↑ XX 1 1 0 1 1 1 0 0 DCh
   Read ID3 1 ↑ 1 XX X X X X X X X X XX
   1 ↑ 1 XX LCD Module / Driver ID [7:0] XX
   Extended Command Set
   Command Function D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 Hex
   RGB Interface 0 1 ↑ XX 1 0 1 1 0 0 0 0 B0h
   Signal Control 1 1 ↑ XX ByPass_MODE RCM [1:0] X VSPL HSPL DPL EPL 40
   0 1 ↑ XX 1 0 1 1 0 0 0 1 B1h
   1 1 ↑ XX X X X X X X DIVA [1:0] 00
   Frame Control
   (In Normal Mode)
   1 1 ↑ XX X X X RTNA [4:0] 1B
   0 1 ↑ XX 1 0 1 1 0 0 1 0 B2h
   1 1 ↑ XX X X X X X X DIVB [1:0] 00
   Frame Control
   (In Idle Mode)
   1 1 ↑ XX X X X RTNB [4:0] 1B
   0 1 ↑ XX 1 0 1 1 0 0 1 1 B3h
   1 1 ↑ XX X X X X X X DIVC [1:0] 00
   Frame Control
   (In Partial Mode)
   1 1 ↑ XX X X X RTNC [4:0] 1B
   0 1 ↑ XX 1 0 1 1 0 1 0 0 B4h
   Display Inversion Control
   1 1 ↑ XX X X X X X NLA NLB NLC 02
   0 1 ↑ XX 1 0 1 1 0 1 0 1 B5h
   1 1 ↑ XX 0 VFP [6:0] 02
   1 1 ↑ XX 0 VBP [6:0] 02
   1 1 ↑ XX 0 0 0 HFP [4:0] 0A
   Blanking Porch Control
   1 1 ↑ XX 0 0 0 HBP [4:0] 14
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 86 of 239
   0 1 ↑ XX 1 0 1 1 0 1 1 0 B6h
   1 1 ↑ XX X X X X PTG [1:0] PT [1:0] 0A
   1 1 ↑ XX REV GS SS SM ISC [3:0] 82
   1 1 ↑ XX X X NL [5:0] 27
   Display Function Control
   1 1 ↑ XX X X PCDIV [5:0] XX
   0 1 ↑ XX 1 0 1 1 0 1 1 1 B7h
   Entry Mode Set
   1 1 ↑ XX X X X X 0 GON DTE GAS 07
   0 1 ↑ XX 1 0 1 1 1 0 0 0 B8h
   Backlight Control 1 1 1 ↑ XX X X X X X X X X XX
   1 1 ↑ XX X X X X TH_UI [3:0] 04
   0 1 ↑ XX 1 0 1 1 1 0 0 1 B9h
   Backlight Control 2 1 1 ↑ XX X X X X X X X X XX
   1 1 ↑ XX TH_MV [3:0] TH_ST [3:0] B8
   0 1 ↑ XX 1 0 1 1 1 0 1 0 BAh
   Backlight Control 3 1 1 ↑ XX X X X X X X X X XX
   1 1 ↑ XX X X X X DTH_UI [3:0] 04
   0 1 ↑ XX 1 0 1 1 1 0 1 1 BBh
   Backlight Control 4 1 1 ↑ XX X X X X X X X X XX
   1 1 ↑ XX DTH_MV [3:0] DTH_ST [3:0] C9
   0 1 ↑ XX 1 0 1 1 1 1 0 0 BCh
   Backlight Control 5 1 1 ↑ XX X X X X X X X X XX
   1 1 ↑ XX DIM2 [3:0] X DIM1 [2:0] 44
   0 1 ↑ XX 1 0 1 1 1 1 1 0 BEh
   Backlight Control 7
   1 1 ↑ XX PWM_DIV [7:0] 0F
   0 1 ↑ XX 1 0 1 1 1 1 1 1 BFh
   Backlight Control 8
   1 1 ↑ XX X X X X X LEDONR LEDONPOL LEDPWMOPL 00
   0 1 ↑ XX 1 1 0 0 0 0 0 0 C0h
   Power Control 1
   1 1 ↑ XX X X VRH [5:0] 26
   0 1 ↑ XX 1 1 0 0 0 0 0 1 C1h
   Power Control 2
   1 1 ↑ XX X X X X X BT [2:0] 00
   0 1 ↑ XX 1 1 0 0 0 1 0 1 C5h
   VCOM Control 1 1 1 ↑ XX X VMH [6:0] 31
   1 1 ↑ XX X VML [6:0] 3C
   0 1 ↑ XX 1 1 0 0 0 1 1 1 C7h
   VCOM Control 2
   1 1 ↑ XX nVM VMF [6:0] C0
   0 1 ↑ XX 1 1 0 1 0 0 0 0 D0h
   NV Memory Write 1 1 ↑ XX X X X X X PGM_ADR [2:0] 00
   1 1 ↑ XX PGM_DATA [7:0] XX
   0 1 ↑ XX 1 1 0 1 0 0 0 1 D1h
   1 1 ↑ XX KEY [23:16] 55
   1 1 ↑ XX KEY [15:8] AA
   NV Memory Protection Key
   1 1 ↑ XX KEY [7:0] 66
   0 1 ↑ XX 1 1 0 1 0 0 1 0 D2h
   1 ↑ 1 XX X X X X X X X X XX
   1 ↑ 1 XX X ID2_CNT [2:0] X ID1_CNT [2:0] XX
   NV Memory Status Read
   1 ↑ 1 XX BUSY VMF_CNT [2:0] X ID3_CNT [2:0] XX
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 87 of 239
   0 ↑ 1 XX 1 1 0 1 0 0 1 1 D3h
   1 ↑ 1 XX X X X X X X X X XX
   1 ↑ 1 XX 0 0 0 0 0 0 0 0 00
   1 ↑ 1 XX 1 0 0 1 0 0 1 1 93
   Read ID4
   1 ↑ 1 XX 0 1 0 0 0 0 0 1 41
   0 1 ↑ XX 1 1 1 0 0 0 0 0 E0h
   1 1 ↑ XX X X X X VP0 [3:0] 08
   1 1 ↑ XX X X VP1 [5:0] 0E
   1 1 ↑ XX X X VP2 [5:0] 12
   1 1 ↑ XX X X X X VP4 [3:0] 05
   1 1 ↑ XX X X X VP6 [4:0] 03
   1 1 ↑ XX X X X X VP13 [3:0] 09
   1 1 ↑ XX X VP20 [6:0] 47
   1 1 ↑ XX VP36 [3:0] VP27 [3:0] 86
   1 1 ↑ XX X VP43 [6:0] 2B
   1 1 ↑ XX X X X X VP50 [3:0] 0B
   1 1 ↑ XX X X X VP57 [4:0] 04
   1 1 ↑ XX X X X X VP59 [3:0] 00
   1 1 ↑ XX X X VP61 [5:0] 00
   1 1 ↑ XX X X VP62 [5:0] 00
   Positive Gamma
   Correction
   1 1 ↑ XX X X X X VP63 [3:0] 00
   0 1 ↑ XX 1 1 1 0 0 0 0 1 E1h
   1 1 ↑ XX X X X X VN0 [3:0] 08
   1 1 ↑ XX X X VN1 [5:0] 1A
   1 1 ↑ XX X X VN2 [5:0] 20
   1 1 ↑ XX X X X X VN4 [3:0] 07
   1 1 ↑ XX X X X VN6 [4:0] 0E
   1 1 ↑ XX X X X X VN13 [3:0] 05
   1 1 ↑ XX X VN20 [6:0] 3A
   1 1 ↑ XX VN36 [3:0] VN27 [3:0] 8A
   1 1 ↑ XX X VN43 [6:0] 40
   1 1 ↑ XX X X X X VN50 [3:0] 04
   1 1 ↑ XX X X X VN57 [4:0] 18
   1 1 ↑ XX X X X X VN59 [3:0] 0F
   1 1 ↑ XX X X VN61 [5:0] 3F
   1 1 ↑ XX X X VN62 [5:0] 3F
   Negative Gamma
   Correction
   1 1 ↑ XX X X X X VN63 [3:0] 0F
   Digital Gamma Control 1 0 1 ↑ XX 1 1 1 0 0 0 1 0 E2h
   1
   st Parameter 1 1 ↑ XX RCA0 [3:0] BCA0 [3:0] XX
   : 1 1 ↑ XX RCAx [3:0] BCAx [3:0] XX
   16th Parameter 1 1 ↑ XX RCA15 [3:0] BCA15 [3:0] XX
   Digital Gamma Control 2 0 1 ↑ XX 1 1 1 0 0 0 1 1 E3h
   1
   st Parameter 1 1 ↑ XX RFA0 [3:0] BFA0 [3:0] XX
   : 1 1 ↑ XX RFAx [3:0] BFAx [3:0] XX
   64th Parameter 1 1 ↑ XX RFA63 [3:0] BFA63 [3:0] XX
   0 1 ↑ XX 1 1 1 1 0 1 1 0 F6h
   1 1 ↑ XX MY_EOR MX_EOR MV_EOR X BGR_EOR X X WEMODE 01
   1 1 ↑ XX X X EPF [1:0] X X MDT [1:0] 00
   Interface Control
   1 1 ↑ XX X X ENDIAN X DM [1:0] RM RIM 00
   Note 1: Undefined commands are treated as NOP (00h) command.
   Note 2: B0 to D9 and DE to FF are for factory use of display supplier. USER can decide if these commands are
   available or they are treated as NOP (00h) commands before shipping to USER. Default value is NOP
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 88 of 239
   (00h).
   Note 3: Commands 10h, 12h, 13h, 26h, 28h, 29h, 30h, 36h (Bit B4 only), 38h and 39h are updated during
   V-SYNC when ILI9341 is in Sleep OUT mode to avoid abnormal visual effects. During Sleep IN mode,
   these commands are updated immediately. Read status (09h), Read display power mode (0Ah), Read
   display MADCTL (0Bh), Read display pixel format (0Ch), Read display image mode (0Dh), Read display
   signal mode (0Eh) and Read display self diagnostic result (0Fh) of these commands are updated
   immediately both in Sleep IN mode and Sleep OUT mode.
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 89 of 239
   8.2. Description of Level 1 Command
   8.2.1. NOP (00h)
   00h NOP (No Operation)
   D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
   Command 0 1 ↑ XX 0 0 0 0 0 0 0 0 00h
   Parameter No Parameter.
   Description
   This command is an empty command; it does not have any effect on the display module. However it can be used to terminate
   Frame Memory Write or Read as described in RAMWR (Memory Write) and RAMRD (Memory Read) Commands.
   X = Don’t care.
   Restriction None
   Register
   Availability
   Status Availability
   Normal Mode On, Idle Mode Off, Sleep Out Yes
   Normal Mode On, Idle Mode On, Sleep Out Yes
   Partial Mode On, Idle Mode Off, Sleep Out Yes
   Partial Mode On, Idle Mode On, Sleep Out Yes
   Sleep In Yes
   Default
   Status Default Value
   Power On Sequence N/A
   SW Reset N/A
   HW Reset N/A
   Flow Chart None
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 90 of 239
   8.2.2. Software Reset (01h)
   01h SWRESET
   D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
   Command 0 1 ↑ XX 0 0 0 0 0 0 0 1 01h
   Parameter No Parameter.
   Description
   When the Software Reset command is written, it causes a software reset. It resets the commands and parameters to their
   S/W Reset default values. (See default tables in each command description.)
   Note: The Frame Memory contents are unaffected by this command
   X = Don’t care.
   Restriction
   It will be necessary to wait 5msec before sending new command following software reset. The display module loads all display
   supplier factory default values to the registers during this 5msec. If Software Reset is applied during Sleep Out mode, it will be
   necessary to wait 120msec before sending Sleep out command. Software Reset Command cannot be sent during Sleep Out
   sequence.
   Register
   Availability
   Status Availability
   Normal Mode On, Idle Mode Off, Sleep Out Yes
   Normal Mode On, Idle Mode On, Sleep Out Yes
   Partial Mode On, Idle Mode Off, Sleep Out Yes
   Partial Mode On, Idle Mode On, Sleep Out Yes
   Sleep In Yes
   Default
   Status Default Value
   Power On Sequence N/A
   SW Reset N/A
   HW Reset N/A
   Flow Chart
   SWRESET(01h)
   Display whole blank screen
   Set
   Commands to
   S/W Default
   Values
   Sleep In Mode
   Command
   Parameter
   Action
   Mode
   Legend
   Sequential transfer
   Display
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 91 of 239
   8.2.3. Read display identification information (04h)
   04h RDDIDIF (Read Display Identification Information)
   D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
   Command 0 1 ↑ XX 0 0 0 0 0 1 0 0 04h
   1
   st Parameter 1 ↑ 1 XX X X X X X X X X X
   2
   ndParameter 1 ↑ 1 XX ID1 [7:0] XX
   3
   rd Parameter 1 ↑ 1 XX ID2 [7:0] XX
   4
   th Parameter 1 ↑ 1 XX ID3 [7:0] XX
   Description
   This read byte returns 24 bits display identification information.
   The 1st parameter is dummy data.
   The 2nd parameter (ID1 [7:0]): LCD module’s manufacturer ID.
   The 3rd parameter (ID2 [7:0]): LCD module/driver version ID.
   The 4th parameter (ID3 [7:0]): LCD module/driver ID.
   Restriction
   Register
   Availability
   Status Availability
   Normal Mode On, Idle Mode Off, Sleep Out Yes
   Normal Mode On, Idle Mode On, Sleep Out Yes
   Partial Mode On, Idle Mode Off, Sleep Out Yes
   Partial Mode On, Idle Mode On, Sleep Out Yes
   Sleep In Yes
   Default
   Status Default Value
   Power On Sequence See description
   SW Reset See description
   HW Reset See description
   Flow Chart
   Command
   Parameter
   Action
   Mode
   Legend
   Sequential transfer
   RDDIDIF(04h)
   1st Parameter: Dummy Read
   2nd Parameter: Send LCD module's manufacturer information
   3rd Parameter: Send panel type and LCM/driver version information
   4th Parameter: Send module/driver information
   Host
   Driver Display
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 92 of 239
   8.2.4. Read Display Status (09h)
   09h RDDST (Read Display Status)
   D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
   Command 0 1 ↑ XX 0 0 0 0 1 0 0 1 09h
   1
   st Parameter 1 ↑ 1 XX X X X X X X X X X
   2
   ndParameter 1 ↑ 1 XX D [31:25] 0 00
   3
   rdParameter 1 ↑ 1 XX 0 D [22:20] D [19:16] 61
   4
   thParameter 1 ↑ 1 XX 0 0 0 0 0 D [10:8] 00
   5
   thParameter 1 ↑ 1 XX D [7:5] 0 0 0 0 0 00
   Description
   This command indicates the current status of the display as described in the table below:
   Bit Description Value Status
   0 Booster OFF
   D31 Booster voltage status
   1 Booster ON
   0 Top to Bottom (When MADCTL B7=’0’)
   D30 Row address order
   1 Bottom to Top (When MADCTL B7=’1’)
   0 Left to Right (When MADCTL B6=’0’).
   D29 Column address order
   1 Right to Left (When MADCTL B6=’1’).
   0 Normal Mode (When MADCTL B5=’0’).
   D28 Row/column exchange
   1 Reverse Mode (When MADCTL B5=’1’).
   0 LCD Refresh Top to Bottom (When MADCTL B4=’0’)
   D27 Vertical refresh
   1 LCD Refresh Bottom to Top (When MADCTL B4=’1’).
   0 RGB (When MADCTL B3=’0’)
   D26 RGB/BGR order
   1 BGR (When MADCTL B3=’1’)
   0 LCD Refresh Left to Right (When MADCTL B2=’0’)
   D25 Horizontal refresh order
   1 LCD Refresh Right to Left (When MADCTL B2=’1’)
   D24 Not used 0 ---
   D23 Not used 0 ---
   D22
   101 16-bit/pixel
   D21
   D20
   Interface color pixel format
   definition
   110 18-bit/pixel
   0 Idle Mode OFF
   D19 Idle mode ON/OFF
   1 Idle Mode ON
   0 Partial Mode OFF
   D18 Partial mode ON/OFF
   1 Partial Mode ON.
   0 Sleep IN Mode
   D17 Sleep IN/OUT
   1 Sleep OUT Mode.
   0 Display Normal Mode OFF.
   D16 Display normal mode ON/OFF
   1 Display Normal Mode ON.
   D15 Vertical scrolling status 0 Scroll OFF
   D14 Not used 0 ---
   D13 Inversion status 0 Not defined
   D12 All pixel ON 0 Not defined
   D11 All pixel OFF 0 Not defined
   0 Display is OFF
   D10 Display ON/OFF
   1 Display is ON
   0 Tearing Effect Line OFF
   D9 Tearing effect line ON/OFF
   1 Tearing Effect ON
   000 GC0
   001 ---
   010 ---
   011 ---
   D[8:6] Gamma curve selection
   other Not defined
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 93 of 239
   0 Mode 1, V-Blanking only
   D5 Tearing effect line mode
   1 Mode 2, both H-Blanking and V-Blanking.
   D4 Not used 0 ---
   D3 Not used 0 ---
   D2 Not used 0 ---
   D1 Not used 0 ---
   D0 Not used 0 ---
   X = Don’t care
   Restriction
   Register
   Availability
   Status Availability
   Normal Mode On, Idle Mode Off, Sleep Out Yes
   Normal Mode On, Idle Mode On, Sleep Out Yes
   Partial Mode On, Idle Mode Off, Sleep Out Yes
   Partial Mode On, Idle Mode On, Sleep Out Yes
   Sleep In Yes
   Default
   Status Default Value
   Power On Sequence 32’h00610000h
   SW Reset 32’h00610000h
   HW Reset 32’h00610000h
   Flow Chart
   Command
   Parameter
   Action
   Mode
   Legend
   Sequential transfer
   RDDST(09h)
   1st Parameter: Dummy Read
   2nd Parameter: Send D[31:25] display status
   3rd Parameter: Send D[19:16] display status
   4th Parameter: Send D[10:8] display status
   5th Parameter: Send D[7:5] display status
   Host
   Driver Display
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 94 of 239
   8.2.5. Read Display Power Mode (0Ah)
   0Ah RDDPM (Read Display Power Mode)
   D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
   Command 0 1 ↑ XX 0 0 0 0 1 0 1 0 0Ah
   1
   st Parameter 1 ↑ 1 XX X X X X X X X X X
   2
   ndParameter 1 ↑ 1 XX D7 D6 D5 D4 D3 D2 D1 D0 08
   Description
   This command indicates the current status of the display as described in the table below::
   Bit Value Description Comment
   0 Booster Off or has a fault. ---
   D7
   1 Booster On and working OK ---
   0 Idle Mode Off. ---
   D6
   1 Idle Mode On. ---
   0 Partial Mode Off. ---
   D5
   1 Partial Mode On. ---
   0 Sleep In Mode ---
   D4
   1 Sleep Out Mode ---
   0 Display Normal Mode Off. ---
   D3
   1 Display Normal Mode On ---
   0 Display is Off. ---
   D2
   1 Display is On ---
   D1 -- Not Defined Set to ‘0’
   D0 -- Not Defined Set to ‘0’
   X = Don’t care
   Restriction
   Register
   Availability
   Status Availability
   Normal Mode On, Idle Mode Off, Sleep Out Yes
   Normal Mode On, Idle Mode On, Sleep Out Yes
   Partial Mode On, Idle Mode Off, Sleep Out Yes
   Partial Mode On, Idle Mode On, Sleep Out Yes
   Sleep In Yes
   Default
   Status Default Value
   Power On Sequence 8’h08h
   SW Reset 8’h08h
   HW Reset 8’h08h
   Flow Chart
   Command
   Parameter
   Action
   Mode
   Legend
   Sequential transfer
   RDDPM(0Ah)
   1st Parameter: Dummy Read
   2nd Parameter: Send D[7:2] display power mode status
   Host
   Driver Display
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 95 of 239
   8.2.6. Read Display MADCTL (0Bh)
   0Bh RDDMADCTL (Read Display MADCTL)
   D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
   Command 0 1 ↑ XX 0 0 0 0 1 0 1 1 0Bh
   1
   st Parameter 1 ↑ 1 XX X X X X X X X X X
   2
   ndParameter 1 ↑ 1 XX D7 D6 D5 D4 D3 D2 D1 D0 00
   Description
   This command indicates the current status of the display as described in the table below:
   Bit Value Description Comment
   0 Top to Bottom (When MADCTL B7=’0’). ---
   D7
   1 Bottom to Top (When MADCTL B7=’1’). ---
   0 Left to Right (When MADCTL B6=’0’) ---
   D6
   1 Right to Left (When MADCTL B6=’1’) ---
   0 Normal Mode (When MADCTL B5=’0’). ---
   D5
   1 Reverse Mode (When MADCTL B5=’1’) ---
   0 LCD Refresh Top to Bottom (When MADCTL B4=’0’) ---
   D4
   1 LCD Refresh Bottom to Top (When MADCTL B4=’1’). ---
   0 RGB (When MADCTL B3=’0’) ---
   D3
   1 BGR (When MADCTL B3=’1’). ---
   0 LCD Refresh Left to Right (When MADCTL B2=’0’). ---
   D2
   1 LCD Refresh Right to Left (When MADCTL B2=’1’). ---
   D1 -- Switching between Segment outputs and RAM Set to ‘0’
   D0 -- Switching between Segment outputs and RAM Set to ‘0’
   X = Don’t care
   Restriction
   Register
   Availability
   Status Availability
   Normal Mode On, Idle Mode Off, Sleep Out Yes
   Normal Mode On, Idle Mode On, Sleep Out Yes
   Partial Mode On, Idle Mode Off, Sleep Out Yes
   Partial Mode On, Idle Mode On, Sleep Out Yes
   Sleep In Yes
   Default
   Status Default Value
   Power On Sequence 8’h00h
   SW Reset No Change
   HW Reset 8’h00h
   Flow Chart
   Command
   Parameter
   Action
   Mode
   Legend
   Sequential transfer
   RDDMADCTL(0Bh)
   1st Parameter: Dummy Read
   2nd Parameter: Send D[7:2] display power mode status
   Host
   Driver Display
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 96 of 239
   8.2.7. Read Display Pixel Format (0Ch)
   0Ch RDDCOLMOD (Read Display Pixel Format)
   D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
   Command 0 1 ↑ XX 0 0 0 0 1 1 0 0 0Ch
   1
   st Parameter 1 ↑ 1 XX X X X X X X X X X
   2
   ndParameter 1 ↑ 1 XX RIM DPI [2:0] 0 DBI [2:0] 06
   Description
   This command indicates the current status of the display as described in the table below:
   RIM DPI [2:0] RGB Interface Format DBI [2:0] MCU Interface Format
   0 0 0 0 Reserved 0 0 0 Reserved
   0 0 0 1 Reserved 0 0 1 Reserved
   0 0 1 0 Reserved 0 1 0 Reserved
   0 0 1 1 Reserved 0 1 1 Reserved
   0 1 0 0 Reserved 1 0 0 Reserved
   0 1 0 1 16 bits / pixel 1 0 1 16 bits / pixel
   0 1 1 0 18 bits / pixel 1 1 0 18 bits / pixel
   0 1 1 1 Reserved 1 1 1 Reserved
   1 1 0 1
   16 bits / pixel
   (6-bit 3 times data transfer)
   1 1 1 0
   18 bits / pixel
   (6-bit 3 times data transfer)
   X = Don’t care
   Restriction
   Register
   Availability
   Status Availability
   Normal Mode On, Idle Mode Off, Sleep Out Yes
   Normal Mode On, Idle Mode On, Sleep Out Yes
   Partial Mode On, Idle Mode Off, Sleep Out Yes
   Partial Mode On, Idle Mode On, Sleep Out Yes
   Sleep In Yes
   Default
   Default Value
   Status
   RIM DPI [2:0] DBI [2:0]
   Power On Sequence 1’b0 3’b000 3’b110
   SW Reset No Chang No Chang No Chang
   HW Reset 1’b0 3’b000 3’b110
   Flow Chart
   Command
   Parameter
   Action
   Mode
   Legend
   Sequential transfer
   RDDCOLMOD(0Ch)
   1st Parameter: Dummy Read
   2nd Parameter: Send D[7:2] display pixel format status
   Host
   Driver Display
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 97 of 239
   8.2.8. Read Display Image Format (0Dh)
   0Dh RDDIM (Read Display Image Mode)
   D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
   Command 0 1 ↑ XX 0 0 0 0 1 1 0 1 0Dh
   1
   st Parameter 1 ↑ 1 XX X X X X X X X X X
   2
   ndParameter 1 ↑ 1 XX 0 0 0 0 0 D [2:0] 00
   Description
   This command indicates the current status of the display as described in the table below:
   D [2:0] Description
   000 Gamma curve 1 (G2.2)
   001 ---
   010 ---
   011 ---
   Other Not defined
   X = Don’t care
   Restriction
   Register
   Availability
   Status Availability
   Normal Mode On, Idle Mode Off, Sleep Out Yes
   Normal Mode On, Idle Mode On, Sleep Out Yes
   Partial Mode On, Idle Mode Off, Sleep Out Yes
   Partial Mode On, Idle Mode On, Sleep Out Yes
   Sleep In Yes
   Default
   Status Default Value
   Power On Sequence 3’b000
   SW Reset 3’b000
   HW Reset 3’b000
   Flow Chart
   Command
   Parameter
   Action
   Mode
   Legend
   Sequential transfer
   RDDIM(0Dh)
   1st Parameter: Dummy Read
   2nd Parameter: Send D[7:0] display image mode status
   Host
   Driver Display
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 98 of 239
   8.2.9. Read Display Signal Mode (0Eh)
   0Eh RDDSM (Read Display Signal Mode)
   D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
   Command 0 1 ↑ XX 0 0 0 0 1 1 1 0 0Eh
   1
   stParameter 1 ↑ 1 XX X X X X X X X X X
   2
   ndParameter 1 ↑ 1 XX D7 D6 D5 D4 D3 D2 D1 D0 00
   Description
   This command indicates the current status of the display as described in the table below:
   Bit Value Description
   0 Tearing effect line OFF D7 1 Tearing effect line ON
   0 Tearing effect line mode 1 D6 1 Tearing effect line mode 2
   0 Horizontal sync. (RGB interface) OFF D5 1 Horizontal sync. (RGB interface) ON
   0 Vertical sync. (RGB interface) OFF D4 1 Vertical sync. (RGB interface) ON
   0 Pixel clock (DOTCLK, RGB interface) OFF D3 1 Pixel clock (DOTCLK, RGB interface) ON
   0 Data enable (DE, RGB interface) OFF D2 1 Data enable (DE, RGB interface) ON
   D1 0 Reserved
   D0 0 Reserved
   X = Don’t care
   Restriction
   Register
   Availability
   Status Availability
   Normal Mode On, Idle Mode Off, Sleep Out Yes
   Normal Mode On, Idle Mode On, Sleep Out Yes
   Partial Mode On, Idle Mode Off, Sleep Out Yes
   Partial Mode On, Idle Mode On, Sleep Out Yes
   Sleep In Yes
   Default
   Status Default Value
   Power On Sequence 8’h00h
   SW Reset 8’h00h
   HW Reset 8’h00h
   Flow Chart
   Command
   Parameter
   Action
   Mode
   Legend
   Sequential transfer
   RDDSM(0Eh)
   1st Parameter: Dummy Read
   2nd Parameter: Send D[7:0] display signal mode status
   Host
   Driver Display

a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 99 of 239
8.2.10. Read Display Self-Diagnostic Result (0Fh)
0Fh RDDSDR (Read Display Self-Diagnostic Result)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 0 0 0 0 1 1 1 1 0Fh
1
stParameter 1 ↑ 1 XX X X X X X X X X X
2
ndParameter 1 ↑ 1 XX D7 D6 0 0 0 0 0 0 00
Description
Bit Description Action
D7 Register Loading Detection Invert the D7 bit if register values loading work properly.
D6 Functionality Detection Invert the D6 bit if the display is functionality
D5 Not Used ‘0’
D4 Not Used ‘0’
D3 Not Used ‘0’
D2 Not Used ‘0’
D1 Not Used ‘0’
D0 Not Used ‘0’
Restriction
Register
Availability
Status Availability
Normal Mode On, Idle Mode Off, Sleep Out Yes
Normal Mode On, Idle Mode On, Sleep Out Yes
Partial Mode On, Idle Mode Off, Sleep Out Yes
Partial Mode On, Idle Mode On, Sleep Out Yes
Sleep In Yes
Default
Status Default Value
Power On Sequence 8’h00h
SW Reset 8’h00h
HW Reset 8’h00h
Flow Chart
Command
Parameter
Action
Mode
Legend
Sequential transfer
RDDSDR(0Fh)
1st Parameter: Dummy Read
2nd Parameter: Send D[7:6] display self-diagnostic status
Host
Driver Display
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 100 of 239
8.2.11. Enter Sleep Mode (10h)
10h SPLIN (Enter Sleep Mode)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 0 0 0 1 0 0 0 0 10h
Parameter No Parameter
Description
This command causes the LCD module to enter the minimum power consumption mode. In this mode e.g. the DC/DC
converter is stopped, Internal oscillator is stopped, and panel scanning is stopped.
MCU interface and memory are still working and the memory keeps its contents.
X = Don’t care
Restriction
This command has no effect when module is already in sleep in mode. Sleep In Mode can only be left by the Sleep Out
Command (11h). It will be necessary to wait 5msec before sending next to command, this is to allow time for the supply
voltages and clock circuits to stabilize. It will be necessary to wait 120msec after sending Sleep Out command (when in Sleep
In Mode) before Sleep In command can be sent.
Register
Availability
Status Availability
Normal Mode On, Idle Mode Off, Sleep Out Yes
Normal Mode On, Idle Mode On, Sleep Out Yes
Partial Mode On, Idle Mode Off, Sleep Out Yes
Partial Mode On, Idle Mode On, Sleep Out Yes
Sleep In Yes
Default
Status Default Value
Power On Sequence Sleep IN Mode
SW Reset Sleep IN Mode
HW Reset Sleep IN Mode
Flow Chart
It takes 120msec to get into Sleep In mode after SLPIN command issued.
Command
Parameter
Action
Mode
Legend
Sequential transfer
SPLIN (10h)
Display whole blank screen
(Automatic No effect to DISP
ON/OFF commands)
Drain charge
from LCD
panel
Stop DC/DC
Converter
Stop Internal
Oscillator
Sleep In Mode
Display
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 101 of 239
8.2.12. Sleep Out (11h)
11h SLPOUT (Sleep Out)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 0 0 0 1 0 0 0 1 11h
Parameter No Parameter
Description
This command turns off sleep mode.
In this mode e.g. the DC/DC converter is enabled, Internal oscillator is started, and panel scanning is started.
X = Don’t care
Restriction
This command has no effect when module is already in sleep out mode. Sleep Out Mode can only be left by the Sleep In
Command (10h). It will be necessary to wait 5msec before sending next command, this is to allow time for the supply voltages
and clock circuits stabilize. The display module loads all display supplier’s factory default values to the registers during this
5msec and there cannot be any abnormal visual effect on the display image if factory default and register values are same
when this load is done and when the display module is already Sleep Out –mode. The display module is doing self-diagnostic
functions during this 5msec. It will be necessary to wait 120msec after sending Sleep In command (when in Sleep Out mode)
before Sleep Out command can be sent.
Register
Availability
Status Availability
Normal Mode On, Idle Mode Off, Sleep Out Yes
Normal Mode On, Idle Mode On, Sleep Out Yes
Partial Mode On, Idle Mode Off, Sleep Out Yes
Partial Mode On, Idle Mode On, Sleep Out Yes
Sleep In Yes
Default
Status Default Value
Power On Sequence Sleep IN Mode
SW Reset Sleep IN Mode
HW Reset Sleep IN Mode
Flow Chart It takes 120msec to become Sleep Out mode after SLPOUT command issued.
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 102 of 239
SPLOUT (11h) Display whole blank screen
for 2 frames (Automatic No
effect to DISP ON/OFF
Commands)
Start up
DC-DC
Converter
Sleep Out Mode
Charge Offset
voltage for
LCD Panel
Start Internal
Oscillator
Display Memory contents in
accordance with the current
command table settings
Command
Parameter
Action
Mode
Legend
Sequential transfer
Display
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 103 of 239
8.2.13. Partial Mode ON (12h)
12h PTLON (Partial Mode On)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 0 0 0 1 0 0 1 0 12h
Parameter No Parameter
Description
This command turns on partial mode The partial mode window is described by the Partial Area command (30H). To leave
Partial mode, the Normal Display Mode On command (13H) should be written.
X = Don’t care
Restriction This command has no effect when Partial mode is active.
Register
Availability
Status Availability
Normal Mode On, Idle Mode Off, Sleep Out Yes
Normal Mode On, Idle Mode On, Sleep Out Yes
Partial Mode On, Idle Mode Off, Sleep Out Yes
Partial Mode On, Idle Mode On, Sleep Out Yes
Sleep In Yes
Default
Status Default Value
Power On Sequence Normal Display Mode ON
SW Reset Normal Display Mode ON
HW Reset Normal Display Mode ON
Flow Chart See Partial Area (30h)
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 104 of 239
8.2.14. Normal Display Mode ON (13h)
13h NORON (Normal Display Mode On)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 0 0 0 1 0 0 1 1 13h
Parameter No Parameter
Description
This command returns the display to normal mode.
Normal display mode on means Partial mode off.
Exit from NORON by the Partial mode On command (12h)
X = Don’t care
Restriction This command has no effect when Normal Display mode is active.
Register
Availability
Status Availability
Normal Mode On, Idle Mode Off, Sleep Out Yes
Normal Mode On, Idle Mode On, Sleep Out Yes
Partial Mode On, Idle Mode Off, Sleep Out Yes
Partial Mode On, Idle Mode On, Sleep Out Yes
Sleep In Yes
Default
Status Default Value
Power On Sequence Normal Display Mode ON
SW Reset Normal Display Mode ON
HW Reset Normal Display Mode ON
Flow Chart See Partial Area (30h)
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 105 of 239
8.2.15. Display Inversion OFF (20h)
20h DINVOFF (Display Inversion OFF)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 0 0 1 0 0 0 0 0 20h
Parameter No Parameter
Description
This command is used to recover from display inversion mode.
This command makes no change of the content of frame memory.
This command doesn’t change any other status.
Memory Display Panel
X = Don’t care
Restriction This command has no effect when module already is inversion OFF mode.
Register
Availability
Status Availability
Normal Mode On, Idle Mode Off, Sleep Out Yes
Normal Mode On, Idle Mode On, Sleep Out Yes
Partial Mode On, Idle Mode Off, Sleep Out Yes
Partial Mode On, Idle Mode On, Sleep Out Yes
Sleep In Yes
Default
Status Default Value
Power On Sequence Display Inversion OFF
SW Reset Display Inversion OFF
HW Reset Display Inversion OFF
Flow Chart INVOFF(20h)
Display Inversion Off Mode
Display Inversion On Mode
Command
Parameter
Action
Mode
Legend
Sequential transfer
Display
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 106 of 239
8.2.16. Display Inversion ON (21h)
21h DINVON (Display Inversion ON)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 0 0 1 0 0 0 0 1 21h
Parameter No Parameter
Description
This command is used to enter into display inversion mode.
This command makes no change of the content of frame memory. Every bit is inverted from the frame memory to the display.
This command doesn’t change any other status.
To exit Display inversion mode, the Display inversion OFF command (20h) should be written.
X = Don’t care
Restriction This command has no effect when module already is inversion ON mode.
Register
Availability
Status Availability
Normal Mode On, Idle Mode Off, Sleep Out Yes
Normal Mode On, Idle Mode On, Sleep Out Yes
Partial Mode On, Idle Mode Off, Sleep Out Yes
Partial Mode On, Idle Mode On, Sleep Out Yes
Sleep In Yes
Default
Status Default Value
Power On Sequence Display Inversion OFF
SW Reset Display Inversion OFF
HW Reset Display Inversion OFF
Flow Chart
INVON(21h)
Display Inversion Off Mode
Display Inversion On Mode Command
Parameter
Action
Mode
Legend
Sequential transfer
Display
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 107 of 239
8.2.17. Gamma Set (26h)
26h GAMSET (Gamma Set)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 0 0 1 0 0 1 1 0 26h
Parameter 1 1 ↑ XX GC [7:0] 01
Description
This command is used to select the desired Gamma curve for the current display. A maximum of 4 fixed gamma curves can
be selected. The curve is selected by setting the appropriate bit in the parameter as described in the Table:
GC [7:0] Curve Selected
01h Gamma curve 1 (G2.2)
02h ---
04h ---
08h ---
Note: All other values are undefined.
X = Don’t care
Restriction
Values of GC [7:0] not shown in table above are invalid and will not change the current selected Gamma curve until valid
value is received.
Register
Availability
Status Availability
Normal Mode On, Idle Mode Off, Sleep Out Yes
Normal Mode On, Idle Mode On, Sleep Out Yes
Partial Mode On, Idle Mode Off, Sleep Out Yes
Partial Mode On, Idle Mode On, Sleep Out Yes
Sleep In Yes
Default
Status Default Value
Power On Sequence 8’h01h
SW Reset 8’h01h
HW Reset 8’h01h
Flow Chart
GAMSET (26h)
1st Parameter: GC[7:0]
New Gamma Curve
Loaded
Command
Parameter
Action
Mode
Legend
Sequential transfer
Display
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 108 of 239
8.2.18. Display OFF (28h)
28h DISPOFF (Display OFF)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 0 0 1 0 1 0 0 0 28h
Parameter No Parameter
Description
This command is used to enter into DISPLAY OFF mode. In this mode, the output from Frame Memory is disabled and blank
page inserted.
This command makes no change of contents of frame memory.
This command does not change any other status.
There will be no abnormal visible effect on the display.
Memory Display Panel
X = Don’t care.
Restriction This command has no effect when module is already in display off mode.
Register
Availability
Status Availability
Normal Mode On, Idle Mode Off, Sleep Out Yes
Normal Mode On, Idle Mode On, Sleep Out Yes
Partial Mode On, Idle Mode Off, Sleep Out Yes
Partial Mode On, Idle Mode On, Sleep Out Yes
Sleep In Yes
Default
Status Default Value
Power On Sequence Display OFF
SW Reset Display OFF
HW Reset Display OFF
Flow Chart
Display On Mode
DISPOFF(28h)
Display Off Mode
Command
Parameter
Action
Mode
Legend
Sequential transfer
Display
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 109 of 239
8.2.19. Display ON (29h)
29h DISPON (Display ON)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 0 0 1 0 1 0 0 1 29h
Parameter No Parameter
Description
This command is used to recover from DISPLAY OFF mode. Output from the Frame Memory is enabled.
This command makes no change of contents of frame memory.
This command does not change any other status
Memory Display Panel
X = Don’t care.
Restriction This command has no effect when module is already in display on mode.
Register
Availability
Status Availability
Normal Mode On, Idle Mode Off, Sleep Out Yes
Normal Mode On, Idle Mode On, Sleep Out Yes
Partial Mode On, Idle Mode Off, Sleep Out Yes
Partial Mode On, Idle Mode On, Sleep Out Yes
Sleep In Yes
Default
Status Default Value
Power On Sequence Display OFF
SW Reset Display OFF
HW Reset Display OFF
Flow Chart
Display Off Mode
DISPON(29h)
Display On Mode
Command
Parameter
Action
Mode
Legend
Sequential transfer
Display
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 110 of 239
8.2.20. Column Address Set (2Ah)
2Ah CASET (Column Address Set)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 0 0 1 0 1 0 1 0 2Ah
1
st Parameter 1 1 ↑ XX SC15 SC14 SC13 SC12 SC11 SC10 SC9 SC8
2
ndParameter 1 1 ↑ XX SC7 SC6 SC5 SC4 SC3 SC2 SC1 SC0
Note1
3
rd Parameter 1 1 ↑ XX EC15 EC14 EC13 EC12 EC11 EC10 EC9 EC8
4
th Parameter 1 1 ↑ XX EC7 EC6 EC5 EC4 EC3 EC2 EC1 EC0
Note1
Description
This command is used to define area of frame memory where MCU can access. This command makes no change on the
other driver status. The values of SC [15:0] and EC [15:0] are referred when RAMWR command comes. Each value
represents one column line in the Frame Memory.
SC[15:0] EC[15:0]
X = Don’t care
Restriction
SC [15:0] always must be equal to or less than EC [15:0].
Note 1: When SC [15:0] or EC [15:0] is greater than 00EFh (When MADCTL’s B5 = 0) or 013Fh
(When MADCTL’s B5 = 1), data of out of range will be ignored
Register
Availability
Status Availability
Normal Mode On, Idle Mode Off, Sleep Out Yes
Normal Mode On, Idle Mode On, Sleep Out Yes
Partial Mode On, Idle Mode Off, Sleep Out Yes
Partial Mode On, Idle Mode On, Sleep Out Yes
Sleep In Yes
Default
Status Default Value
Power On Sequence SC [15:0]=0000h EC [15:0]=00EFh
SW Reset SC [15:0]=0000h
If MADCTL’s B5 = 0: EC [15:0]=00EFh
If MADCTL’s B5 = 1: EC [15:0]=013Fh
HW Reset SC [15:0]=0000h EC [15:0]=00EFh
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 111 of 239
Flow Chart
CASET (2Ah)
1st Parameter: SC[15:8]
2nd Parameter: SC[7:0]
3rd Parameter: EC[15:8]
4th Parmeter EC[7:0]
PASET (2Bh)
1st Parameter: SP[15:8]
2nd Parameter: SP[7:0]
3rd Parameter: EP[15:8]
4th Parameter: EP[7:0]
RAMWR(2Ch)
Image Data
D1[17:0],D2[17:0]..Dn[17:0]
Any Commend
If
Needed
If
Needed
Command
Parameter
Action
Mode
Legend
Sequential transfer
Display
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 112 of 239
8.2.21. Page Address Set (2Bh)
2Bh PASET (Page Address Set)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 0 0 1 0 1 0 1 1 2Bh
1
st Parameter 1 1 ↑ XX SP15 SP14 SP13 SP12 SP11 SP10 SP9 SP8
2
ndParameter 1 1 ↑ XX SP7 SP6 SP5 SP4 SP3 SP2 SP1 SP0
Note1
3
rdParameter 1 1 ↑ XX EP15 EP14 EP13 EP12 EP11 EP10 EP9 EP8
4
th Parameter 1 1 ↑ XX EP7 EP6 EP5 EP4 EP3 EP2 EP1 EP0
Note1
Description
This command is used to define area of frame memory where MCU can access. This command makes no change on the
other driver status. The values of SP [15:0] and EP [15:0] are referred when RAMWR command comes. Each value
represents one Page line in the Frame Memory.
SP[15:0]
EP[15:0]
X = Don’t care
Restriction
SP [15:0] always must be equal to or less than EP [15:0]
Note 1: When SP [15:0] or EP [15:0] is greater than 013Fh (When MADCTL’s B5 = 0) or 00EFh (When MADCTL’s B5 = 1),
data of out of range will be ignored.
Register
Availability
Status Availability
Normal Mode On, Idle Mode Off, Sleep Out Yes
Normal Mode On, Idle Mode On, Sleep Out Yes
Partial Mode On, Idle Mode Off, Sleep Out Yes
Partial Mode On, Idle Mode On, Sleep Out Yes
Sleep In Yes
Default
Status Default Value
Power On Sequence SP [15:0]=0000h EP [15:0]=013Fh
SW Reset SP [15:0]=0000h
If MADCTL’s B5 = 0: EP [15:0]=013Fh
If MADCTL’s B5 = 1: EP [15:0]=00EFh
HW Reset SP [15:0]=0000h EP [15:0]=013Fh
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 113 of 239
Flow Chart
CASET (2Ah)
1st Parameter: SC[15:8]
2nd Parameter: SC[7:0]
3rd Parameter: EC[15:8]
4th Parmeter EC[7:0]
PASET (2Bh)
1st Parameter: SP[15:8]
2nd Parameter: SP[7:0]
3rd Parameter: EP[15:8]
4th Parameter: EP[7:0]
RAMWR(2Ch)
Image Data
D1[17:0],D2[17:0]..Dn[17:0]
Any Commend
If
Needed
If
Needed
Command
Parameter
Action
Mode
Legend
Sequential transfer
Display
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 114 of 239
8.2.22. Memory Write (2Ch)
2Ch RAMWR (Memory Write)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 0 0 1 0 1 1 0 0 2Ch
1
st Parameter 1 1 ↑ D1 [17:0] XX
: 1 1 ↑ Dx [17:0] XX
N
th Parameter 1 1 ↑ Dn [17:0] XX
Description
This command is used to transfer data from MCU to frame memory. This command makes no change to the other driver
status. When this command is accepted, the column register and the page register are reset to the Start Column/Start
Page positions. The Start Column/Start Page positions are different in accordance with MADCTL setting.) Then D [17:0] is
stored in frame memory and the column register and the page register incremented. Sending any other command can stop
frame Write. X = Don’t care.
Restriction In all color modes, there is no restriction on length of parameters.
Register
Availability
Status Availability
Normal Mode On, Idle Mode Off, Sleep Out Yes
Normal Mode On, Idle Mode On, Sleep Out Yes
Partial Mode On, Idle Mode Off, Sleep Out Yes
Partial Mode On, Idle Mode On, Sleep Out Yes
Sleep In Yes
Default
Status Default Value
Power On Sequence Contents of memory is set randomly
SW Reset Contents of memory is not cleared
HW Reset Contents of memory is not cleared
Flow Chart
CASET (2Ah)
1st Parameter: SC[15:8]
2nd Parameter: SC[7:0]
3rd Parameter: EC[15:8]
4th Parmeter EC[7:0]
PASET (2Bh)
1st Parameter: SP[15:8]
2nd Parameter: SP[7:0]
3rd Parameter: EP[15:8]
4th Parameter: EP[7:0]
RAMWR(2Ch)
Image Data
D1[17:0],D2[17:0]..Dn[17:0]
Any Commend
If
Needed
If
Needed
Command
Parameter
Action
Mode
Legend
Sequential transfer
Display
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 115 of 239
8.2.23. Color Set (2Dh)
2Dh RGBSET (Color Set)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 0 0 1 0 1 1 0 1 2Dh
1
st Parameter 1 1 ↑ XX 0 0 R00 [5:0] XX
n
th Parameter 1 1 ↑ XX 0 0 Rnn [5:0] XX
32ndParameter 1 1 ↑ XX 0 0 R31 [5:0] XX
33rdParameter 1 1 ↑ XX 0 0 G00 [5:0] XX
n
th Parameter 1 1 ↑ XX 0 0 Gnn [5:0] XX
96thParameter 1 1 ↑ XX 0 0 G64 [5:0] XX
97thParameter 1 1 ↑ XX 0 0 B00 [5:0] XX
n
th Parameter 1 1 ↑ XX 0 0 Bnn [5:0] XX
128thParameter 1 1 ↑ XX 0 0 B31 [5:0] XX
Description
This command is used to define the LUT for 16-bit to 18-bit color depth conversion.
128 bytes must be written to the LUT regardless of the color mode. Only the values in Section 7.4 are referred.
This command has no effect on other commands, parameter and contents of frame memory. Visible change takes effect
next time the frame memory is written to.
Restriction
Register
Availability
Status Availability
Normal Mode On, Idle Mode Off, Sleep Out Yes
Normal Mode On, Idle Mode On, Sleep Out Yes
Partial Mode On, Idle Mode Off, Sleep Out Yes
Partial Mode On, Idle Mode On, Sleep Out Yes
Sleep In Yes
Default
Status Default Value
Power On Sequence Random values
SW Reset Contents of LUT protected
HW Reset Random values
Flow Chart
RGBSET (2Dh)
1st Parameter: R00[5:0]
:
32nd Parameter: R31[5:0]
33rd Parameter: G00[5:0]
:
96th Parameter: G63[5:0]
97th Parameter: B00[5:0]
:
128th Parameter: B31[5:0]
Command
Parameter
Action
Mode
Legend
Sequential transfer
Display
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 116 of 239
8.2.24. Memory Read (2Eh)
2Eh RAMRD (Memory Read)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 0 0 1 0 1 1 1 0 2Eh
1
stParameter 1 1 ↑ XX X X X X X X X X X
2
ndParameter 1 1 ↑ D1 [17:0] XX
: 1 1 ↑ Dx [17:0] XX
(N+1)th
Parameter
1 1 ↑ Dn [17:0] XX
Description
This command transfers image data from ILI9341’s frame memory to the host processor starting at the pixel location
specified by preceding set_column_address and set_page_address commands.
If Memory Access control B5 = 0:
The column and page registers are reset to the Start Column (SC) and Start Page (SP), respectively. Pixels are read from
frame memory at (SC, SP). The column register is then incremented and pixels read from the frame memory until the
column register equals the End Column (EC) value. The column register is then reset to SC and the page register is
incremented. Pixels are read from the frame memory until the page register equals the End Page (EP) value or the host
processor sends another command.
If Memory Access Control B5 = 1:
The column and page registers are reset to the Start Column (SC) and Start Page (SP), respectively. Pixels are read from
frame memory at (SC, SP). The page register is then incremented and pixels read from the frame memory until the page
register equals the End Page (EP) value. The page register is then reset to SP and the column register is incremented.
Pixels are read from the frame memory until the column register equals the End Column (EC) value or the host processor
sends another command.
Restriction There is no restriction on length of parameters.
Register
Availability
Status Availability
Normal Mode On, Idle Mode Off, Sleep Out Yes
Normal Mode On, Idle Mode On, Sleep Out Yes
Partial Mode On, Idle Mode Off, Sleep Out Yes
Partial Mode On, Idle Mode On, Sleep Out Yes
Sleep In Yes
Default
Status Default Value
Power On Sequence Contents of memory is set randomly
SW Reset Contents of memory is set randomly
HW Reset Contents of memory is set randomly
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 117 of 239
Flow Chart
RAMRD (2Eh)
Dummy Read
Image Data
D1[17:0],D2[17:0]..Dn[17:0]
Any Command
Command
Parameter
Action
Mode
Legend
Sequential transfer
Display
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 118 of 239
8.2.25. Partial Area (30h)
30h PLTAR (Partial Area)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 0 0 1 1 0 0 0 0 30h
1
st Parameter 1 1 ↑ XX SR15 SR14 SR13 SR12 SR11 SR10 SR9 SR8 00
2
ndParameter 1 1 ↑ XX SR7 SR6 SR5 SR4 SR3 SR2 SR1 SR0 00
3
rdParameter 1 1 ↑ XX ER15 ER14 ER13 ER12 ER11 ER10 ER9 ER8 01
4
th Parameter 1 1 ↑ XX ER7 ER6 ER5 ER4 ER3 ER2 ER1 ER0 3F
Description
This command defines the partial mode’s display area. There are 2 parameters associated with this command, the first
defines the Start Row (SR) and the second the End Row (ER), as illustrated in the figures below. SR and ER refer to the
Frame Memory Line Pointer.
If End Row>Start Row when MADCTL B4=0:-
SR[15:0]
ER[15:0]
Partial
Area
End Row
Start Row
If End Row>Start Row when MADCTL B4=1:-
SR[15:0]
ER[15:0]
Partial
Area
End Row
Start Row
If End Row<Start Row when MADCTL B4=0:-
SR[15:0]
ER[15:0]
Partial
End Row Area
Start Row
Partial
Area
If End Row = Start Row then the Partial Area will be one row deep.
X = Don’t care.
Restriction SR [15…0] and ER [15…0] cannot be 0000h nor exceed 013Fh.
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 119 of 239
Register
Availability
Status Availability
Normal Mode On, Idle Mode Off, Sleep Out Yes
Normal Mode On, Idle Mode On, Sleep Out Yes
Partial Mode On, Idle Mode Off, Sleep Out Yes
Partial Mode On, Idle Mode On, Sleep Out Yes
Sleep In Yes
Default
Default Value
Status
SR [15:0] ER [15:0]
Power On Sequence 16’h0000h 16’h013Fh
SW Reset 16’h 0000h 16’h 013Fh
HW Reset 16’h 0000h 16’h 013Fh
Flow Chart

1. To Enter Partial Mode
   PLTAR(30h)
   PTLON(12h)
   1st Parameter: SR[15:8]
   2nd Parameter: SR[7:0]
   3rd Parameter: ER[15:8]
   4th Parameter: ER[7:0]
   Partial Mode
   Command
   Parameter
   Action
   Mode
   Legend
   Sequential transfer
   Display
2. To Leave Partial Mode
   DISPOFF(28h)
   Image Data
   D1[17:0],D2[17:0]..Dn[17:0]
   RAMRW(2Ch)
   Partial Mode
   NORON(13h)
   Partial Mode OFF
   DISPON(29h)
   Command
   Parameter
   Action
   Mode
   Legend
   Sequential transfer
   Display
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 120 of 239
   8.2.26. Vertical Scrolling Definition (33h)
   33h VSCRDEF (Vertical Scrolling Definition)
   D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
   Command 0 1 ↑ XX 0 0 1 1 0 0 1 1 33h
   1
   stParameter 1 ↑ 1 XX TFA [15:8] 00
   2
   ndParameter 1 ↑ 1 XX TFA [7:0] 00
   3
   rdParameter 1 ↑ 1 XX VSA [15:8] 01
   4
   thParameter 1 ↑ 1 XX VSA [7:0] 40
   5
   thParameter 1 ↑ 1 XX BFA [15:8] 00
   6
   thParameter 1 ↑ 1 XX BFA [7:0] 00
   Description
   This command defines the Vertical Scrolling Area of the display.
   When MADCTL B4=0
   The 1st & 2nd parameter TFA [15...0] describes the Top Fixed Area (in No. of lines from Top of the Frame Memory and
   Display).
   The 3rd & 4th parameter VSA [15...0] describes the height of the Vertical Scrolling Area (in No. of lines of the Frame
   Memory [not the display] from the Vertical Scrolling Start Address). The first line read from Frame Memory appears
   immediately after the bottom most line of the Top Fixed Area.
   The 5th & 6th parameter BFA [15...0] describes the Bottom Fixed Area (in No. of lines from Bottom of the Frame Memory
   and Display). TFA, VSA and BFA refer to the Frame Memory Line Pointer.
   Top Fixed Area
   Bottom Fixed Area
   TFA[15:0]
   BFA[15:0]
   (0, 0)
   First line
   read from
   memory Scroll Area
   When MADCTL B4=1
   The 1st & 2nd parameter TFA [15...0] describes the Top Fixed Area (in No. of lines from Bottom of the Frame Memory and
   Display).
   The 3rd & 4th parameter VSA [15...0] describes the height of the Vertical Scrolling Area (in No. of lines of the Frame
   Memory [not the display] from the Vertical Scrolling Start Address). The first line read from Frame Memory appears
   immediately after the top most line of the Top Fixed Area.
   The 5th & 6th parameter BFA [15...0] describes the Bottom Fixed Area (in No. of lines from Top of the
   Frame Memory and Display).
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 121 of 239
   Bottom Fixed Area
   Top Fixed Area
   TFA[15:0]
   BFA[15:0]
   (0, 0)
   First line
   read from
   memory
   Scroll Area
   X = Don’t care
   Restriction
   Register
   Availability
   Status Availability
   Normal Mode On, Idle Mode Off, Sleep Out Yes
   Normal Mode On, Idle Mode On, Sleep Out Yes
   Partial Mode On, Idle Mode Off, Sleep Out Yes
   Partial Mode On, Idle Mode On, Sleep Out Yes
   Sleep In Yes
   Default
   Default Value
   Status
   TFA [15:0] VSA [15:0] BFA [15:0]
   Power On Sequence 16’h0000h 16’h0140h 16’h0000h
   SW Reset 16’h0000h 16’h0140h 16’h0000h
   HW Reset 16’h0000h 16’h0140h 16’h0000h
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 122 of 239
   Flow Chart
3. To enter Vertical Scroll Mode :
   Normal Mode
   CASET(2Ah)
   1st & 2nd parameter :
   SC[15:0]
   3rd & 4th Parameter
   EC[15:0]
   PASET(2Bh)
   1st & 2nd parameter :
   SP[15:0]
   3rd & 4th Parameter
   EP[15:0]
   RAMRW(2Ch)
   Scroll Image Data
   VSCRSADD(37h)
   1st & 2nd parameter :
   VSP[15:0]
   Only
   required
   for nonrolling
   scrolling
   Command
   Parameter
   Action
   Mode
   Legend
   Sequential transfer
   Display
   Normal Mode
   Only
   required
   for nonrolling
   scrolling
   VSCRDEF (33h)
   1st & 2nd parameter :
   TFA[15:0]
   3rd & 4th Parameter
   VSA[15:0]
   5th & 6th Parameter
   BFA[15:0]
   MADCTL
   Parameter
   Optional : It may be
   necessary to
   redefine the Frame
   Memory Write
   Direction
   Note : The Frame Memory Window size ,must be defined correctly otherwise undesirable image will be displayed.
4. Continuous Scroll :
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 123 of 239
   Scroll Mode
   PASET (2Bh)
   1st & 2nd parameter :
   SP[15:0]
   3rd & 4th Parameter
   EP[15:0]
   CASET (2Ah)
   1st & 2nd parameter :
   SC[15:0]
   3rd & 4th Parameter
   EC[15:0]
   RAMRW
   Scroll Image Data
   VSCRSADD(37h)
   Command
   Parameter
   Action
   Mode
   Legend
   Sequential transfer
   Display
   3.To Leave Vertical Scroll Mode:
   Scroll Mode
   DISOFF(28h)
   MORON(12h)/PTLON(12h)
   Image Data
   D1[17:0],D2[17:0]...Dn[17:0]
   DISON(29h)
   Scroll Mode Off
   RAMRW(2Ch)
   (Optional )
   To prevent Tearing Effect Image
   Display
   Note: Scroll Mode can be left by both the Normal Display Mode ON (13h) and Partial Mode ON (12h) commands.
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 124 of 239
   8.2.27. Tearing Effect Line OFF (34h)
   34h TEOFF (Tearing Effect Line OFF)
   D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
   Command 0 1 ↑ XX 0 0 1 1 0 1 0 0 34h
   Parameter No Parameter
   Description
   This command is used to turn OFF (Active Low) the Tearing Effect output signal from the TE signal line.
   X = Don’t care.
   Restriction This command has no effect when Tearing Effect output is already OFF.
   Register
   Availability
   Status Availability
   Normal Mode On, Idle Mode Off, Sleep Out Yes
   Normal Mode On, Idle Mode On, Sleep Out Yes
   Partial Mode On, Idle Mode Off, Sleep Out Yes
   Partial Mode On, Idle Mode On, Sleep Out Yes
   Sleep In Yes
   Default
   Status Default Value
   Power On Sequence OFF
   SW Reset OFF
   HW Reset OFF
   Flow Chart
   TE Line Output ON
   TEOFF(34h)
   TE Line Output OFF
   Command
   Parameter
   Action
   Mode
   Legend
   Sequential transfer
   Display
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 125 of 239
   8.2.28. Tearing Effect Line ON (35h)
   35h TEON (Tearing Effect Line ON)
   D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
   Command 0 1 ↑ XX 0 0 1 1 0 1 0 1 35h
   Parameter 1 1 ↑ XX 0 0 0 0 0 0 0 M 00
   Description
   This command is used to turn ON the Tearing Effect output signal from the TE signal line. This output is not affected by
   changing MADCTL bit B4. The Tearing Effect Line On has one parameter which describes the mode of the Tearing Effect
   Output Line.
   When M=0:
   The Tearing Effect Output line consists of V-Blanking information only:
   Vertical Time Scale
   tvdl tvdh
   When M=1:
   The Tearing Effect Output Line consists of both V-Blanking and H-Blanking information:
   Vertical Time Scale
   tvdl tvdh
   Note: During Sleep In Mode with Tearing Effect Line On, Tearing Effect Output pin will be active Low.
   X = Don’t care.
   Restriction This command has no effect when Tearing Effect output is already ON
   Register
   Availability
   Status Availability
   Normal Mode On, Idle Mode Off, Sleep Out Yes
   Normal Mode On, Idle Mode On, Sleep Out Yes
   Partial Mode On, Idle Mode Off, Sleep Out Yes
   Partial Mode On, Idle Mode On, Sleep Out Yes
   Sleep In Yes
   Default
   Status Default Value
   Power On Sequence OFF
   SW Reset OFF
   HW Reset OFF
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 126 of 239
   Flow Chart
   TE Line Output OFF
   TEON(35h)
   TE Line Output ON
   1st Parameter: M bit
   Command
   Parameter
   Action
   Mode
   Legend
   Sequential transfer
   Display
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 127 of 239
   8.2.29. Memory Access Control (36h)
   36h MADCTL (Memory Access Control)
   D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
   Command 0 1 ↑ XX 0 0 1 1 0 1 1 0 36h
   Parameter 1 1 ↑ XX MY MX MV ML BGR MH 0 0 00
   Description
   This command defines read/write scanning direction of frame memory.
   This command makes no change on the other driver status.
   Bit Name Description
   MY Row Address Order
   MX Column Address Order
   MV Row / Column Exchange
   These 3 bits control MCU to memory write/read direction.
   ML Vertical Refresh Order LCD vertical refresh direction control.
   BGR RGB-BGR Order Color selector switch control
   (0=RGB color filter panel, 1=BGR color filter panel)
   MH Horizontal Refresh ORDER LCD horizontal refreshing direction control.
   Note: When BGR bit is changed, the new setting is active immediately without update the content in Frame Memory again.
   X = Don’t care.
   MV(Vertical refresh order bit)="0" MV(Vertical refresh order bit)="1"
   overwrite
   memory display memory display
   Top-Left (0,0) Top-Left (0,0)
   memory display
   Send last (320)
   Send 3rd (3)
   Send 2nd (2)
   Send 1st (1)
   Top-Left (0,0) Top-Left (0,0)
   memory display
   Send 1st (1)
   Send 3rd (3)
   Send 2nd (2)
   Send last (320)
   (example) (example)
   ML(Vertical refresh order bit)="0" ML(Vertical refresh order bit)="1"
   R G B Driver IC R G B
   SIG1 SIG2 SIG240
   R G B
   LCD Panel
   SIG1 SIG2 SIG240
   R G B
   R G B
   R G B
   R G B
   R G B
   R G B Driver IC R G B
   SIG1 SIG2 SIG240
   G B R
   LCD Panel
   SIG1 SIG2 SIG240
   B G R
   B R G
   B G R
   B G R
   B G R
   BGR(RGB-BGR Order control bit)="0" BGR(RGB-BGR Order control bit)="1"
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 128 of 239
   display
   Send 1st (1)
   Send 2nd (2)
   Send 3rd (3)
   Send last (240)
   Top-Left (0,0)
   memory
   Top-Left (0,0)
   display
   Send last (240)
   Send 3rd (3)
   Send 2nd (2)
   Send 1st (1)
   Top-Left (0,0)
   memory
   Top-Left (0,0)
   MH(Horizontal refresh order control bit)="0" MH(Horizontal refresh order control bit)="1"
   Note: Top-Left (0,0) means a physical memory location.
   Restriction
   Register
   Availability
   Status Availability
   Normal Mode On, Idle Mode Off, Sleep Out Yes
   Normal Mode On, Idle Mode On, Sleep Out Yes
   Partial Mode On, Idle Mode Off, Sleep Out Yes
   Partial Mode On, Idle Mode On, Sleep Out Yes
   Sleep In Yes
   Default
   Status Default Value
   Power On Sequence 8’h00h
   SW Reset No change
   HW Reset 8’h00h
   Flow Chart
   MADCTR(36h)
   1st Parameter: MY, MX, MV, ML, RGB, MH
   Command
   Parameter
   Action
   Mode
   Legend
   Sequential transfer
   Display
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 129 of 239
   8.2.30. Vertical Scrolling Start Address (37h)
   37h VSCRSADD (Vertical Scrolling Start Address)
   D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
   Command 0 1 ↑ XX 0 0 1 1 0 1 1 1 37h
   1
   stParameter 1 ↑ 1 XX VSP [15:8] 00
   2
   ndParameter 1 ↑ 1 XX VSP [7:0] 00
   Description
   This command is used together with Vertical Scrolling Definition (33h). These two commands describe the scrolling area
   and the scrolling mode. The Vertical Scrolling Start Address command has one parameter which describes the address of
   the line in the Frame Memory that will be written as the first line after the last line of the Top Fixed Area
   on the display as illustrated below:-
   When MADCTL B4=0
   Example:
   When Top Fixed Area = Bottom Fixed Area = 00, Vertical Scrolling Area = 320 and VSP=’3’.
   Frame Memory
   (0, 0)
   Line Pointer
   VSP[15:0]
   (0, 319)
   0
   Pointer
   B4=0
   1
   2
   3
   4
   ..
   ..
   317
   318
   319
   Display
   When MADCTL B4=1
   Example:
   When Top Fixed Area = Bottom Fixed Area = 00, Vertical Scrolling Area = 320 and VSP=’3’.
   Frame Memory
   (0, 319)
   Line Pointer
   VSP[15:0]
   (0, 0)
   0
   Pointer
   B4=1
   1
   2
   3
   4
   ..
   ..
   317
   318
   319
   Display
   Note: (1) When new Pointer position and Picture Data are sent, the result on the display will happen at the next Panel Scan
   to avoid tearing effect. VSP refers to the Frame Memory line Pointer.
   (2) This command is ignored when the ILI9341 enters Partial mode.
   X = Don’t care
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 130 of 239
   Restriction
   Register
   Availability
   Status Availability
   Normal Mode On, Idle Mode Off, Sleep Out Yes
   Normal Mode On, Idle Mode On, Sleep Out Yes
   Partial Mode On, Idle Mode Off, Sleep Out No
   Partial Mode On, Idle Mode On, Sleep Out No
   Sleep In Yes
   Default
   Default Value
   Status
   VSP [15:0]
   Power On Sequence 16’h0000h
   SW Reset 16’h0000h
   HW Reset 16’h0000h
   Flow Chart See Vertical Scrolling Definition (33h) description.
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 131 of 239
   8.2.31. Idle Mode OFF (38h)
   38h IDMOFF (Idle Mode OFF)
   D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
   Command 0 1 ↑ XX 0 0 1 1 1 0 0 0 38h
   Parameter No Parameter
   Description
   This command is used to recover from Idle mode on.
   In the idle off mode, LCD can display maximum 262,144 colors.
   X = Don’t care.
   Restriction This command has no effect when module is already in idle off mode.
   Register
   Availability
   Status Availability
   Normal Mode On, Idle Mode Off, Sleep Out Yes
   Normal Mode On, Idle Mode On, Sleep Out Yes
   Partial Mode On, Idle Mode Off, Sleep Out Yes
   Partial Mode On, Idle Mode On, Sleep Out Yes
   Sleep In Yes
   Default
   Status Default Value
   Power On Sequence Idle mode OFF
   SW Reset Idle mode OFF
   HW Reset Idle mode OFF
   Flow Chart
   IDMOFF(38h)
   Idle mode on
   Idle mode off
   Command
   Parameter
   Action
   Mode
   Legend
   Sequential transfer
   Display
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 132 of 239
   8.2.32. Idle Mode ON (39h)
   39h IDMON (Idle Mode ON)
   D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
   Command 0 1 ↑ XX 0 0 1 1 1 0 0 1 39h
   Parameter No Parameter
   Description
   This command is used to enter into Idle mode on.
   In the idle on mode, color expression is reduced. The primary and the secondary colors using MSB of each R, G and B in the
   Frame Memory, 8 color depth data is displayed.
   Memory Panel Display
   Memory Contents vs. Display Color
   R5 R4 R3 R2 R1 R0 G5 G4 G3 G2 G1 G0 B5 B4 B3 B2 B1 B0
   Black 0XXXXX 0XXXXX 0XXXXX
   Blue 0XXXXX 0XXXXX 1XXXXX
   Red 1XXXXX 0XXXXX 0XXXXX
   Magenta 1XXXXX 0XXXXX 1XXXXX
   Green 0XXXXX 1XXXXX 0XXXXX
   Cyan 0XXXXX 1XXXXX 1XXXXX
   Yellow 1XXXXX 1XXXXX 0XXXXX
   White 1XXXXX 1XXXXX 1XXXXX
   X = Don’t care.
   Restriction This command has no effect when module is already in idle off mode.
   Register
   Availability
   Status Availability
   Normal Mode On, Idle Mode Off, Sleep Out Yes
   Normal Mode On, Idle Mode On, Sleep Out Yes
   Partial Mode On, Idle Mode Off, Sleep Out Yes
   Partial Mode On, Idle Mode On, Sleep Out Yes
   Sleep In Yes
   Default
   Status Default Value
   Power On Sequence Idle mode OFF
   SW Reset Idle mode OFF
   HW Reset Idle mode OFF
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 133 of 239
   Flow Chart IDMON(39h)
   Idle mode off
   Idle mode on
   Command
   Parameter
   Action
   Mode
   Legend
   Sequential transfer
   Display
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 134 of 239
   8.2.33. COLMOD: Pixel Format Set (3Ah)
   3Ah PIXSET (Pixel Format Set)
   D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
   Command 0 1 ↑ XX 0 0 1 1 1 0 1 0 3Ah
   Parameter 1 1 ↑ XX 0 DPI [2:0] 0 DBI [2:0] 66
   Description
   This command sets the pixel format for the RGB image data used by the interface. DPI [2:0] is the pixel format select of RGB
   interface and DBI [2:0] is the pixel format of MCU interface. If a particular interface, either RGB interface or MCU interface, is
   not used then the corresponding bits in the parameter are ignored. The pixel format is shown in the table below.
   DPI [2:0] RGB Interface Format DBI [2:0] MCU Interface Format
   0 0 0 Reserved 0 0 0 Reserved
   0 0 1 Reserved 0 0 1 Reserved
   0 1 0 Reserved 0 1 0 Reserved
   0 1 1 Reserved 0 1 1 Reserved
   1 0 0 Reserved 1 0 0 Reserved
   1 0 1 16 bits / pixel 1 0 1 16 bits / pixel
   1 1 0 18 bits / pixel 1 1 0 18 bits / pixel
   1 1 1 Reserved 1 1 1 Reserved
   If using RGB Interface must selection serial interface.
   X = Don’t care
   Restriction
   Register
   Availability
   Status Availability
   Normal Mode On, Idle Mode Off, Sleep Out Yes
   Normal Mode On, Idle Mode On, Sleep Out Yes
   Partial Mode On, Idle Mode Off, Sleep Out Yes
   Partial Mode On, Idle Mode On, Sleep Out Yes
   Sleep In Yes
   Default
   Default Value
   Status
   DPI [2:0] DBI [2:0]
   Power On Sequence 3’b110 3’b110
   SW Reset No Change No Change
   HW Reset 3’b110 3’b110
   Flow Chart
   COLMOD (3Ah)
   DPI[2:0] RGB pixel format
   DBI[2:0] MCU pixel format
   Command
   Parameter
   Action
   Mode
   Legend
   Sequential transfer
   Display
   Any Command
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 135 of 239
   8.2.34. Write_Memory_Continue (3Ch)
   3Ch Write_Memory_Continue
   D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
   Command 0 1 ↑ XX 0 0 1 1 1 1 0 0 3Ch
   1
   st Parameter 1 1 ↑
   D1
   [17..8]
   D1
   [7]
   D1
   [6]
   D1
   [5]
   D1
   [4]
   D1
   [3]
   D1
   [2]
   D1
   [1]
   D1
   [0]
   000
   3FF
   X
   th Parameter 1 1 ↑
   Dx
   [17..8]
   Dx
   [7]
   Dx
   [6]
   Dx
   [5]
   Dx
   [4]
   Dx
   [3]
   Dx
   [2]
   Dx
   [1]
   Dx
   [0]
   000
   3FF
   N
   th Parameter 1 1 ↑
   Dn
   [17..8]
   Dn
   [7]
   Dn
   [6]
   Dn
   [5]
   Dn
   [4]
   Dn
   [3]
   Dn
   [2]
   Dn
   [1]
   Dn
   [0]
   000
   3FF
   Description
   This command transfers image data from the host processor to the display module’s frame memory continuing from the
   pixel location following the previous write_memory_continue or write_memory_start command.
   If set_address_mode B5 = 0:
   Data is written continuing from the pixel location after the write range of the previous write_memory_start or
   write_memory_continue. The column register is then incremented and pixels are written to the frame memory until the
   column register equals the End Column (EC) value. The column register is then reset to SC and the page register is
   incremented. Pixels are written to the frame memory until the page register equals the End Page (EP) value and the
   column register equals the EC value, or the host processor sends another command. If the number of pixels exceeds (EC –
   SC + 1) _ (EP – SP + 1) the extra pixels are ignored.
   If set_address_mode B5 = 1:
   Data is written continuing from the pixel location after the write range of the previous write_memory_start or
   write_memory_continue. The page register is then incremented and pixels are written to the frame memory until the page
   register equals the End Page (EP) value. The page register is then reset to SP and the column register is incremented.
   Pixels are written to the frame memory until the column register equals the End column (EC) value and the page register
   equals the EP value, or the host processor sends another command. If the number of pixels exceeds (EC – SC + 1) _ (EP –
   SP + 1) the extra pixels are ignored.
   Sending any other command can stop frame Write.
   Frame Memory Access and Interface setting (B3h), WEMODE=0
   When the transfer number of data exceeds (EC-SC+1)_(EP-SP+1), the exceeding data will be ignored.
   Frame Memory Access and Interface setting (B3h), WEMODE=1
   When the transfer number of data exceeds (EC-SC+1)_(EP-SP+1), the column and page number will be reset, and the
   exceeding data will be written into the following column and page.
   Restriction
   A write_memory_start should follow a set_column_address, set_page_address or set_address_mode to define the write
   address. Otherwise, data written with write_memory_continue is written to undefined addresses.
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 136 of 239
   Register
   Availability
   Status Availability
   Normal Mode On, Idle Mode Off, Sleep Out Yes
   Normal Mode On, Idle Mode On, Sleep Out Yes
   Partial Mode On, Idle Mode Off, Sleep Out Yes
   Partial Mode On, Idle Mode On, Sleep Out Yes
   Sleep In No
   Default
   Status Default Value
   Power On Sequence Random value
   SW Reset No change
   HW Reset No change
   Flow Chart
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 137 of 239
   8.2.35. Read_Memory_Continue (3Eh)
   3Eh Read_Memory_Continue
   D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
   Command 0 1 ↑ XX 0 0 1 1 1 1 1 0 3Eh
   1
   st Parameter 1 ↑ 1 XX X X X X X X X X X
   2
   nd Parameter 1 ↑ 1
   D1
   [17..8]
   D1
   [7]
   D1
   [6]
   D1
   [5]
   D1
   [4]
   D1
   [3]
   D1
   [2]
   D1
   [1]
   D1
   [0]
   000
   3FF
   x
   st Parameter 1 ↑ 1
   Dx
   [17..8]
   Dx
   [7]
   Dx
   [6]
   Dx
   [5]
   Dx
   [4]
   Dx
   [3]
   Dx
   [2]
   Dx
   [1]
   Dx
   [0]
   000
   3FF
   N
   st Parameter 1 ↑ 1
   Dn
   [17..8]
   Dn
   [7]
   Dn
   [6]
   Dn
   [5]
   Dn
   [4]
   Dn
   [3]
   Dn
   [2]
   Dn
   [1]
   Dn
   [0]
   000
   3FF
   Description
   This command transfers image data from the display module’s frame memory to the host processor continuing from the
   location following the previous read_memory_continue (3Eh) or read_memory_start (2Eh) command.
   If set_address_mode B5 = 0:
   Pixels are read continuing from the pixel location after the read range of the previous read_memory_start or
   read_memory_continue. The column register is then incremented and pixels are read from the frame memory until the
   column register equals the End Column (EC) value. The column register is then reset to SC and the page register is
   incremented. Pixels are read from the frame memory until the page register equals the End Page (EP) value and the
   column register equals the EC value, or the host processor sends another command.
   If set_address_mode B5 = 1:
   Pixels are read continuing from the pixel location after the read range of the previous read_memory_start or
   read_memory_continue. The page register is then incremented and pixels are read from the frame memory until the page
   register equals the End Page (EP) value. The page register is then reset to SP and the column register is incremented.
   Pixels are read from the frame memory until the column register equals the End Column (EC) value and the page register
   equals the EP value, or the host processor sends another command.
   This command makes no change to the other driver status.
   Restriction
   A read_memory_start should follow a set_column_address, set_page_address or set_address_mode to define the read
   location. Otherwise, data read with read_memory_continue is undefined.
   Register
   Availability
   Status Availability
   Normal Mode On, Idle Mode Off, Sleep Out Yes
   Normal Mode On, Idle Mode On, Sleep Out Yes
   Partial Mode On, Idle Mode Off, Sleep Out Yes
   Partial Mode On, Idle Mode On, Sleep Out Yes
   Sleep In Yes
   Default
   Status Default Value
   Power On Sequence Random data
   SW Reset No change
   HW Reset No change
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 138 of 239
   Flow Chart
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 139 of 239
   8.2.36. Set_Tear_Scanline (44h)
   44h Set_Tear_Scanline
   D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
   Command 0 1 ↑ XX 0 1 0 0 0 1 0 0 44h
   1
   st Parameter 1 1 ↑ XX 0 0 0 0 0 0 0
   STS
   [8]
   00
   2
   nd Parameter 1 1 ↑ XX
   STS
   [7]
   STS
   [6]
   STS
   [5]
   STS
   [4]
   STS
   [3]
   STS
   [2]
   STS
   [1]
   STS
   [0]
   00
   Description
   This command turns on the display Tearing Effect output signal on the TE signal line when the display reaches line STS.
   The TE signal is not affected by changing set_address_mode bit B4. The Tearing Effect Line On has one parameter that
   describes the Tearing Effect Output Line mode.
   tvdl tvdh
   Vertical Time Scale
   Note that set_tear_scanline with STS=0 is equivalent to set_tear_on with M=0.
   The Tearing Effect Output line shall be active low when the display module is in Sleep mode.
   Restriction -
   Register
   Availability
   Status Availability
   Normal Mode On, Idle Mode Off, Sleep Out Yes
   Normal Mode On, Idle Mode On, Sleep Out Yes
   Partial Mode On, Idle Mode Off, Sleep Out Yes
   Partial Mode On, Idle Mode On, Sleep Out Yes
   Sleep In Yes
   Default
   Status Default Value
   Power On Sequence STS [8:0]=0000h
   SW Reset STS [8:0]=0000h
   HW Reset STS [8:0]=0000h
   Flow Chart
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 140 of 239
   8.2.37. Get_Scanline (45h)
   45h Get_Scanline
   D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
   Command 0 1 ↑ XX 0 1 0 0 0 1 0 1 45h
   1
   st Parameter 1 ↑ 1 XX X X X X X X X X X
   2
   nd Parameter 1 ↑ 1 XX 0 0 0 0 0 0
   GTS
   [9]
   GTS
   [8]
   00
   3
   rd Parameter 1 ↑ 1 XX
   GTS
   [7]
   GTS
   [6]
   GTS
   [5]
   GTS
   [4]
   GTS
   [3]
   GTS
   [2]
   GTS
   [1]
   GTS
   [0]
   00
   Description
   The display returns the current scan line, GTS, used to update the display device. The total number of scan lines on a
   display device is defined as VSYNC + VBP + VACT + VFP. The first scan line is defined as the first line of V-Sync and is
   denoted as Line 0.
   When in Sleep Mode, the value returned by get_scanline is undefined.
   Restriction None
   Register
   Availability
   Status Availability
   Normal Mode On, Idle Mode Off, Sleep Out Yes
   Normal Mode On, Idle Mode On, Sleep Out Yes
   Partial Mode On, Idle Mode Off, Sleep Out Yes
   Partial Mode On, Idle Mode On, Sleep Out Yes
   Sleep In Yes
   Default
   Default Value
   Status
   GTS [9:0]
   Power On Sequence GTS [9:0]=0000h
   SW Reset GTS [9:0]=0000h
   HW Reset GTS [9:0]=0000h
   Flow Chart

a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 141 of 239
8.2.38. Write Display Brightness (51h)
51h WRDISBV (Write Display Brightness)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 0 1 0 1 0 0 0 1 51h
Parameter 1 1 ↑ XX DBV[7] DBV[6] DBV[5] DBV[4] DBV[3] DBV[2] DBV[1] DBV[0] 00
Description
This command is used to adjust the brightness value of the display.
It should be checked what is the relationship between this written value and output brightness of the display. This relationship
is defined on the display module specification.
In principle relationship is that 00h value means the lowest brightness and FFh value means the highest brightness.
Restriction None
Register
Availability
Status Availability
Normal Mode On, Idle Mode Off, Sleep Out Yes
Normal Mode On, Idle Mode On, Sleep Out Yes
Partial Mode On, Idle Mode Off, Sleep Out Yes
Partial Mode On, Idle Mode On, Sleep Out Yes
Sleep In Yes
Default
Default Value
Status
DBV [7:0]
Power On Sequence 8’h00h
SW Reset 8’h00h
HW Reset 8’h00h
Flow Chart

a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 142 of 239
8.2.39. Read Display Brightness (52h)
52h RDDISBV (Read Display Brightness Value)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 0 1 0 1 0 0 1 0 52h
1
st Parameter 1 ↑ 1 XX X X X X X X X X X
2
nd Parameter 1 ↑ 1 XX DBV[7] DBV[6] DBV[5] DBV[4] DBV[3] DBV[2] DBV[1] DBV[0] 00
Description
This command returns the brightness value of the display.
It should be checked what the relationship between this returned value and output brightness of the display. This
relationship is defined on the display module specification.
In principle the relationship is that 00h value means the lowest brightness and FFh value means the highest brightness.
Restriction
The display module is sending 2nd parameter value on the data lines if the MCU wants to read more than one parameter
(= more than 2 RDX cycle) on DBI Mode.
Only 2nd parameter is sent on DSI (The 1st parameter is not sent).
Register
Availability
Status Availability
Normal Mode On, Idle Mode Off, Sleep Out Yes
Normal Mode On, Idle Mode On, Sleep Out Yes
Partial Mode On, Idle Mode Off, Sleep Out Yes
Partial Mode On, Idle Mode On, Sleep Out Yes
Sleep In Yes
Default
Default Value
Status
DBV [7:0]
Power On Sequence 8’h00h
SW Reset 8’h00h
HW Reset 8’h00h
Flow Chart

a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 143 of 239
8.2.40. Write CTRL Display (53h)
53h WRCTRLD (Write Control Display)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 0 1 0 1 0 0 1 1 53h
Parameter 1 1 ↑ XX 0 0 BCTRL 0 DD BL 0 0 00
Description
This command is used to control display brightness.
BCTRL: Brightness Control Block On/Off, This bit is always used to switch brightness for display.
0 = Off (Brightness registers are 00h, DBV[7..0])
1 = On (Brightness registers are active, according to the other parameters.)
DD: Display Dimming, only for manual brightness setting
DD = 0: Display Dimming is off
DD = 1: Display Dimming is on
BL: Backlight Control On/Off
0 = Off (Completely turn off backlight circuit. Control lines must be low. )
1 = On
Dimming function is adapted to the brightness registers for display when bit BCTRL is changed at DD=1, e.g. BCTRL: 0 
1 or 1 0.
When BL bit change from “On” to “Off”, backlight is turned off without gradual dimming, even if dimming-on (DD=1) are
selected.
Restriction None
Register
Availability
Status Availability
Normal Mode On, Idle Mode Off, Sleep Out Yes
Normal Mode On, Idle Mode On, Sleep Out Yes
Partial Mode On, Idle Mode Off, Sleep Out Yes
Partial Mode On, Idle Mode On, Sleep Out Yes
Sleep In Yes
Default
Default Value
Status
BCTRL DD BL
Power On Sequence 1’b0 1’b0 1’b0
SW Reset 1’b0 1’b0 1’b0
HW Reset 1’b0 1’b0 1’b0
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 144 of 239
Flow Chart
WRCTRLD
BCTRL,DD,BL
Command
Parameter
Action
Mode
Legend
Sequential transfer
Display
New Control
Value Loaded
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 145 of 239
8.2.41. Read CTRL Display (54h)
54h RDCTRLD (Read Control Display)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 0 1 0 1 0 1 0 0 54h
1
st Parameter 1 ↑ 1 XX X X X X X X X X XX
2
nd Parameter 1 ↑ 1 XX 0 0 BCTRL 0 DD BL 0 0 00
Description
This command is used to return brightness setting.
BCTRL: Brightness Control Block On/Off,
‘0’ = Off (Brightness registers are 00h)
‘1’ = On (Brightness registers are active, according to the DBV[7..0] parameters.)
DD: Display Dimming
‘0’ = Display Dimming is off
‘1’ = Display Dimming is on
BL: Backlight On/Off
‘0’ = Off (Completely turn off backlight circuit. Control lines must be low. )
‘1’ = On
Restriction
The display module is sending 2nd parameter value on the data lines if the MCU wants to read more than one parameter
(= more than 2 RDX cycle) on DBI.
Only 2nd parameter is sent on DSI (The 1st parameter is not sent).
Register
Availability
Status Availability
Normal Mode On, Idle Mode Off, Sleep Out Yes
Normal Mode On, Idle Mode On, Sleep Out Yes
Partial Mode On, Idle Mode Off, Sleep Out Yes
Partial Mode On, Idle Mode On, Sleep Out Yes
Sleep In Yes
Default
Default Value
Status
BCTRL DD BL
Power On Sequence 1’b0 1’b0 1’b0
SW Reset 1’b0 1’b0 1’b0
HW Reset 1’b0 1’b0 1’b0
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 146 of 239
Flow Chart

a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 147 of 239
8.2.42. Write Content Adaptive Brightness Control (55h)
55h WRCABC (Write Content Adaptive Brightness Control)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 0 1 0 1 0 1 0 1 55h
Parameter 1 1 ↑ XX 0 0 0 0 0 0 C [1] C [0] 00
Description
This command is used to set parameters for image content based adaptive brightness control functionality.
There is possible to use 4 different modes for content adaptive image functionality, which are defined on a table
below.
C [1:0] Default Value
2’b00 Off
2’b01 User Interface Image
2’b10 Still Picture
2’b11 Moving Image
Restriction None
Register
Availability
Status Availability
Normal Mode On, Idle Mode Off, Sleep Out Yes
Normal Mode On, Idle Mode On, Sleep Out Yes
Partial Mode On, Idle Mode Off, Sleep Out Yes
Partial Mode On, Idle Mode On, Sleep Out Yes
Sleep In Yes
Default
Status Default Value
Power On Sequence C [1:0]=00h
SW Reset C [1:0]=00h
HW Reset C [1:0]=00h
Flow Chart

a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 148 of 239
8.2.43. Read Content Adaptive Brightness Control (56h)
56h RDCABC (Read Content Adaptive Brightness Control)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 0 1 0 1 0 1 1 0 56h
1
st Parameter 1 ↑ 1 XX X X X X X X X X XX
2
nd Parameter 1 ↑ 1 XX 0 0 0 0 0 0 C [1] C [0] 00
Description
This command is used to read the settings for image content based adaptive brightness control functionality.
It is possible to use 4 different modes for content adaptive image functionality, which are defined on a table below.
C [1:0] Default Value
2’b00 Off
2’b01 User Interface Image
2’b10 Still Picture
2’b11 Moving Image
Restriction
The display module is sending 2nd parameter value on the data lines if the MCU wants to read more than one parameter
(= more than 2 RDX cycle) on DBI.
Only 2nd parameter is sent on DSI (The 1st parameter is not sent).
Register
Availability
Status Availability
Normal Mode On, Idle Mode Off, Sleep Out Yes
Normal Mode On, Idle Mode On, Sleep Out Yes
Partial Mode On, Idle Mode Off, Sleep Out Yes
Partial Mode On, Idle Mode On, Sleep Out Yes
Sleep In Yes
Default
Status Default Value
Power On Sequence C [1:0]=00h
SW Reset C [1:0]=00h
HW Reset C [1:0]=00h
Flow Chart

a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 149 of 239
8.2.44. Write CABC Minimum Brightness (5Eh)
5Eh Backlight Control 1
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 0 1 0 1 1 1 1 0 5Eh
Parameter 1 1 ↑ XX CMB
[7]
CMB
[6]
CMB
[5]
CMB
[4]
CMB
[3]
CMB
[2]
CMB
[1]
CMB
[0] 00
Description
This command is used to set the minimum brightness value of the display for CABC function.
CMB[7:0]: CABC minimum brightness control, this parameter is used to avoid too much brightness reduction.
When CABC is active, CABC cannot reduce the display brightness to less than CABC minimum brightness setting. Image
processing function is worked as normal, even if the brightness cannot be changed.
This function does not affect to the other function, manual brightness setting. Manual brightness can be set the display
brightness to less than CABC minimum brightness. Smooth transition and dimming function can be worked as normal.
When display brightness is turned off (BCTRL=0 of “Write CTRL Display (53h)”), CABC minimum brightness setting is
ignored.
In principle relationship is that 00h value means the lowest brightness for CABC and FFh value means the highest
brightness for CABC.
Register
Availability
Status Availability
Normal Mode On, Idle Mode Off, Sleep Out Yes
Normal Mode On, Idle Mode On, Sleep Out Yes
Partial Mode On, Idle Mode Off, Sleep Out Yes
Partial Mode On, Idle Mode On, Sleep Out Yes
Sleep In Yes
Default
Default Value
Status
CMB [7:0]
Power On Sequence 8’h00h
SW Reset No Change
HW Reset 8’h00h
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 150 of 239
8.2.45. Read CABC Minimum Brightness (5Fh)
5Fh Backlight Control 1
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 0 1 0 1 1 1 1 1 5Fh
1
stParameter 1 ↑ 1 XX X X X X X X X X X
2
ndParameter 1 ↑ 1 XX CMB
[7]
CMB
[6]
CMB
[5]
CMB
[4]
CMB
[3]
CMB
[2]
CMB
[1]
CMB
[0] 00
Description
This command returns the minimum brightness value of CABC function.
In principle the relationship is that 00h value means the lowest brightness and FFh value means the highest brightness.
CMB[7:0] is CABC minimum brightness specified with “Write CABC minimum brightness (5Eh)” command. In principle
relationship is that 00h value means the lowest brightness for CABC and FFh value means the highest brightness for
CABC.
Register
Availability
Status Availability
Normal Mode On, Idle Mode Off, Sleep Out Yes
Normal Mode On, Idle Mode On, Sleep Out Yes
Partial Mode On, Idle Mode Off, Sleep Out Yes
Partial Mode On, Idle Mode On, Sleep Out Yes
Sleep In Yes
Default
Default Value
Status
CMB [7:0]
Power On Sequence 8’h00h
SW Reset No Change
HW Reset 8’h00h
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 151 of 239
8.2.46. Read ID1 (DAh)
DAh RDID1 (Read ID1)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 1 1 0 1 1 0 1 0 DAh
1
stParameter 1 ↑ 1 XX X X X X X X X X X
2
ndParameter 1 ↑ 1 XX ID1 [7:0] XX
Description
This read byte identifies the LCD module’s manufacturer ID and it is specified by User
The 1st parameter is dummy data.
The 2nd parameter is LCD module’s manufacturer ID.
X = Don’t care
Restriction
Register
Availability
Status Availability
Normal Mode On, Idle Mode Off, Sleep Out Yes
Normal Mode On, Idle Mode On, Sleep Out Yes
Partial Mode On, Idle Mode Off, Sleep Out Yes
Partial Mode On, Idle Mode On, Sleep Out Yes
Sleep In Yes
Default
Status
Default Value
(Before MTP program)
Default Value
(After MTP program)
Power On Sequence 8’h00h MTP value
SW Reset 8’h00h MTP value
HW Reset 8’h00h MTP value
Flow Chart
Command
Parameter
Action
Mode
Legend
Sequential transfer
RDID1(DAh)
1st Parameter: Dummy Read
2nd Parameter: Send ID1[7:0]
Host
Driver Display
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 152 of 239
8.2.47. Read ID2 (DBh)
DBh RDID2 (Read ID2)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 1 1 0 1 1 0 1 1 DBh
1
st Parameter 1 ↑ 1 XX X X X X X X X X X
2
ndParameter 1 ↑ 1 XX 1 ID2 [6:0] XX
Description
This read byte is used to track the LCD module/driver version. It is defined by display supplier (with User’s agreement) and
changes each time a revision is made to the display, material or construction specifications.
The 1st parameter is dummy data.
The 2nd parameter is LCD module/driver version ID and the ID parameter range is from 80h to FFh.
The ID2 can be programmed by MTP function.
X = Don’t care
Restriction
Register
Availability
Status Availability
Normal Mode On, Idle Mode Off, Sleep Out Yes
Normal Mode On, Idle Mode On, Sleep Out Yes
Partial Mode On, Idle Mode Off, Sleep Out Yes
Partial Mode On, Idle Mode On, Sleep Out Yes
Sleep In Yes
Default
Status
Default Value
(Before MTP program)
Default Value
(After MTP program)
Power On Sequence 8’h80h MTP value
SW Reset 8’h80h MTP value
HW Reset 8’h80h MTP value
Flow Chart
Command
Parameter
Action
Mode
Legend
Sequential transfer
RDID2(DBh)
1st Parameter: Dummy Read
2nd Parameter: Send ID2[7:0]
Host
Driver Display
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 153 of 239
8.2.48. Read ID3 (DCh)
DCh RDID3 (Read ID3)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 1 1 0 1 1 1 0 0 DCh
1
stParameter 1 ↑ 1 XX X X X X X X X X X
2
ndParameter 1 ↑ 1 XX ID3 [7:0] XX
Description
This read byte identifies the LCD module/driver and It is specified by User.
The 1st parameter is dummy data.
The 2nd parameter is LCD module/driver ID.
The ID3 can be programmed by MTP function.
X = Don’t care
Restriction
Register
Availability
Status Availability
Normal Mode On, Idle Mode Off, Sleep Out Yes
Normal Mode On, Idle Mode On, Sleep Out Yes
Partial Mode On, Idle Mode Off, Sleep Out Yes
Partial Mode On, Idle Mode On, Sleep Out Yes
Sleep In Yes
Default
Status
Default Value
(Before MTP program)
Default Value
(After MTP program)
Power On Sequence 8’h00h MTP value
SW Reset 8’h00h MTP value
HW Reset 8’h00h MTP value
Flow Chart
Command
Parameter
Action
Mode
Legend
Sequential transfer
RDID3(DCh)
1st Parameter: Dummy Read
2nd Parameter: Send ID3[7:0]
Host
Driver Display
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 154 of 239
8.3. Description of Level 2 Command
8.3.1. RGB Interface Signal Control (B0h)
B0h IFMODE (Interface Mode Control)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 1 0 1 1 0 0 0 0 B0h
Parameter 1 1 ↑ XX ByPass_MODE
RCM
[1]
RCM
[0]
0 VSPL HSPL DPL EPL 40
Description
Sets the operation status of the display interface. The setting becomes effective as soon as the command is received.
EPL: DE polarity (“0”= High enable for RGB interface, “1”= Low enable for RGB interface)
DPL: DOTCLK polarity set (“0”= data fetched at the rising time, “1”= data fetched at the falling time)
HSPL: HSYNC polarity (“0”= Low level sync clock, “1”= High level sync clock)
VSPL: VSYNC polarity (“0”= Low level sync clock, “1”= High level sync clock)
RCM [1:0]: RGB interface selection (refer to the RGB interface section).
ByPass_MODE: Select display data path whether Memory or Direct to Shift register when RGB Interface is used.
ByPass_MODE Display Data Path
0 Direct to Shift Register (default)
1 Memory
Restriction EXTC should be high to enable this command
Register
Availability
Status Availability
Normal Mode ON, Idle Mode OFF, Sleep OUT Yes
Normal Mode ON, Idle Mode ON, Sleep OUT Yes
Partial Mode ON, Idle Mode OFF, Sleep OUT Yes
Partial Mode ON, Idle Mode ON, Sleep OUT Yes
Sleep IN Yes
Default
Default Value Status ByPass_MODE RCM [1:0] VSPL HSPL DPL EPL
Power ON Sequence 1’b0 2’b10 1’b0 1’b0 1’b0 1’b1
SW Reset 1’b0 2’b10 1’b0 1’b0 1’b0 1’b1
HW Reset 1’b0 2’b10 1’b0 1’b0 1’b0 1’b1
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 155 of 239
8.3.2. Frame Rate Control (In Normal Mode/Full Colors) (B1h)
B1h FRMCTR1 (Frame Rate Control (In Normal Mode / Full colors))
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 1 0 1 1 0 0 0 1 B1h
1
st Parameter 1 1 ↑ XX 0 0 0 0 0 0 DIVA [1:0] 00
2
nd Parameter 1 1 ↑ XX 0 0 0 RTNA [4:0] 1B
Description
Formula to calculate frame frequency:
Frame Rate=
Clocks per line x Division ratio x (Lines VBP VFP)
fosc

- - Sets the division ratio for internal clocks of Normal mode at MCU interface.
    fosc : internal oscillator frequency
    Clocks per line : RTNA setting
    Division ratio : DIVA setting
    Lines : total driving line number
    VBP : back porch line number
    VFP : front porch line number
    RTNA [4:0] Frame Rate (Hz) RTNA [4:0] Frame Rate (Hz)
    1 0 0 0 0 119 1 1 0 0 0 79
    1 0 0 0 1 112 1 1 0 0 1 76
    1 0 0 1 0 106 1 1 0 1 0 73
    1 0 0 1 1 100 1 1 0 1 1 70(default)
    1 0 1 0 0 95 1 1 1 0 0 68
    1 0 1 0 1 90 1 1 1 0 1 65
    1 0 1 1 0 86 1 1 1 0 1 63
    1 0 1 1 1 83 1 1 1 1 1 61
    DIVA [1:0] : division ratio for internal clocks when Normal mode.
    DIVA [1:0] Division Ratio
    0 0 fosc
    0 1 fosc / 2
    1 0 fosc / 4
    1 1 fosc / 8
    RTNA [4:0] : RTNA[4:0] is used to set 1H (line) period of Normal mode at MCU interface.
    RTNA [4:0]
    Clock per
    Line
    RTNA [4:0]
    Clock per
    Line
    RTNA [4:0]
    Clock per
    Line
    0 0 0 0 0 Setting prohibited 0 1 0 1 1 Setting prohibited 1 0 1 1 0 22 clocks
    0 0 0 0 1 Setting prohibited 0 1 1 0 0 Setting prohibited 1 0 1 1 1 23 clocks
    0 0 0 1 0 Setting prohibited 0 1 1 0 1 Setting prohibited 1 1 0 0 0 24 clocks
    0 0 0 1 1 Setting prohibited 0 1 1 1 0 Setting prohibited 1 1 0 0 1 25 clocks
    0 0 1 0 0 Setting prohibited 0 1 1 1 1 Setting prohibited 1 1 0 1 0 26 clocks
    0 0 1 0 1 Setting prohibited 1 0 0 0 0 16 clocks 1 1 0 1 1 27 clocks
    0 0 1 1 0 Setting prohibited 1 0 0 0 1 17 clocks 1 1 1 0 0 28 clocks
    0 0 1 1 1 Setting prohibited 1 0 0 1 0 18 clocks 1 1 1 0 1 29 clocks
    0 1 0 0 0 Setting prohibited 1 0 0 1 1 19 clocks 1 1 1 1 0 30 clocks
    0 1 0 0 1 Setting prohibited 1 0 1 0 0 20 clocks 1 1 1 1 1 31 clocks
    0 1 0 1 0 Setting prohibited 1 0 1 0 1 21 clocks
    a-Si TFT LCD Single Chip Driver
    240RGBx320 Resolution and 262K color ILI9341
    The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
    reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
    Page 156 of 239
    Restriction EXTC should be high to enable this command
    Register
    Availability
    Status Availability
    Normal Mode ON, Idle Mode OFF, Sleep OUT Yes
    Normal Mode ON, Idle Mode ON, Sleep OUT Yes
    Partial Mode ON, Idle Mode OFF, Sleep OUT Yes
    Partial Mode ON, Idle Mode ON, Sleep OUT Yes
    Sleep IN Yes
    Default
    Default Value
    Status
    DIVA [1:0] RTNA [4:0]
    Power ON Sequence 2’b00 5’h1Bh
    SW Reset 2’b00 5’h1Bh
    HW Reset 2’b00 5’h1Bh
    a-Si TFT LCD Single Chip Driver
    240RGBx320 Resolution and 262K color ILI9341
    The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
    reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
    Page 157 of 239
    8.3.3. Frame Rate Control (In Idle Mode/8 colors) (B2h)
    B2h FRMCTR2 (Frame Rate Control (In Idle Mode / 8l colors))
    D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
    Command 0 1 ↑ XX 1 0 1 1 0 0 1 0 B2h
    1
    st Parameter 1 1 ↑ XX 0 0 0 0 0 0 DIVB [1:0] 00
    2
    ndParameter 1 1 ↑ XX 0 0 0 RTNB [4:0] 1B
    Description
    Formula to calculate frame frequency
    Frame Rate=
    Clocks per line x Division ratio x (Lines VBP VFP)
    fosc
- - Sets the division ratio for internal clocks of Idle mode at MCU interface.
    fosc : internal oscillator frequency
    Clocks per line : RTNB setting
    Division ratio : DIVB setting
    Lines : total driving line number
    VBP : back porch line number
    VFP : front porch line number
    RTNB [4:0] Frame Rate (Hz) RTNB [4:0] Frame Rate (Hz)
    1 0 0 0 0 119 1 1 0 0 0 79
    1 0 0 0 1 112 1 1 0 0 1 76
    1 0 0 1 0 106 1 1 0 1 0 73
    1 0 0 1 1 100 1 1 0 1 1 70(default)
    1 0 1 0 0 95 1 1 1 0 0 68
    1 0 1 0 1 90 1 1 1 0 1 65
    1 0 1 1 0 86 1 1 1 0 1 63
    1 0 1 1 1 83 1 1 1 1 1 61
    DIVB [1:0]: division ratio for internal clocks when Idle mode.
    DIVB [1:0] Division Ratio
    0 0 fosc
    0 1 fosc / 2
    1 0 fosc / 4
    1 1 fosc / 8
    RTNB [4:0]: RTNB[4:0] is used to set 1H (line) period of Idle mode at MCU interface.
    RTNB [4:0]
    Clock per
    Line
    RTNB [4:0]
    Clock per
    Line
    RTNB [4:0]
    Clock per
    Line
    0 0 0 0 0 Setting prohibited 0 1 0 1 1 Setting prohibited 1 0 1 1 0 22 clocks
    0 0 0 0 1 Setting prohibited 0 1 1 0 0 Setting prohibited 1 0 1 1 1 23 clocks
    0 0 0 1 0 Setting prohibited 0 1 1 0 1 Setting prohibited 1 1 0 0 0 24 clocks
    0 0 0 1 1 Setting prohibited 0 1 1 1 0 Setting prohibited 1 1 0 0 1 25 clocks
    0 0 1 0 0 Setting prohibited 0 1 1 1 1 Setting prohibited 1 1 0 1 0 26 clocks
    0 0 1 0 1 Setting prohibited 1 0 0 0 0 16 clocks 1 1 0 1 1 27 clocks
    0 0 1 1 0 Setting prohibited 1 0 0 0 1 17 clocks 1 1 1 0 0 28 clocks
    0 0 1 1 1 Setting prohibited 1 0 0 1 0 18 clocks 1 1 1 0 1 29 clocks
    0 1 0 0 0 Setting prohibited 1 0 0 1 1 19 clocks 1 1 1 1 0 30 clocks
    0 1 0 0 1 Setting prohibited 1 0 1 0 0 20 clocks 1 1 1 1 1 31 clocks
    0 1 0 1 0 Setting prohibited 1 0 1 0 1 21 clocks
    a-Si TFT LCD Single Chip Driver
    240RGBx320 Resolution and 262K color ILI9341
    The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
    reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
    Page 158 of 239
    Restriction EXTC should be high to enable this command
    Register
    Availability
    Status Availability
    Normal Mode ON, Idle Mode OFF, Sleep OUT Yes
    Normal Mode ON, Idle Mode ON, Sleep OUT Yes
    Partial Mode ON, Idle Mode OFF, Sleep OUT Yes
    Partial Mode ON, Idle Mode ON, Sleep OUT Yes
    Sleep IN Yes
    Default
    Default Value
    Status
    DIVB [1:0] RTNB [4:0]
    Power ON Sequence 2’b00 5’h1Bh
    SW Reset 2’b00 5’h1Bh
    HW Reset 2’b00 5’h1Bh
    a-Si TFT LCD Single Chip Driver
    240RGBx320 Resolution and 262K color ILI9341
    The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
    reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
    Page 159 of 239
    8.3.4. Frame Rate control (In Partial Mode/Full Colors) (B3h)
    B3h FRMCTR3 (Frame Rate Control (In Partial Mode / Full colors))
    D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
    Command 0 1 ↑ XX 1 0 1 1 0 0 1 1 B3h
    1
    st Parameter 1 1 ↑ XX 0 0 0 0 0 0 DIVC [1:0] 00
    2
    ndParameter 1 1 ↑ XX 0 0 0 RTNC [4:0] 1B
    Description
    Formula to calculate frame frequency:
    Frame Rate=
    Clocks per line x Division ratio x (Lines VBP VFP)
    fosc
- - Sets the division ratio for internal clocks of Partial mode (Idle mode off) at MCU interface.
    fosc : internal oscillator frequency
    Clocks per line : RTNC setting
    Division ratio : DIVC setting
    Lines : total driving line number
    VBP : back porch line number
    VFP : front porch line number
    RTNC [4:0] Frame Rate (Hz) RTNC [4:0] Frame Rate (Hz)
    1 0 0 0 0 119 1 1 0 0 0 79
    1 0 0 0 1 112 1 1 0 0 1 76
    1 0 0 1 0 106 1 1 0 1 0 73
    1 0 0 1 1 100 1 1 0 1 1 70(default)
    1 0 1 0 0 95 1 1 1 0 0 68
    1 0 1 0 1 90 1 1 1 0 1 65
    1 0 1 1 0 86 1 1 1 0 1 63
    1 0 1 1 1 83 1 1 1 1 1 61
    DIVC [1:0]: division ratio for internal clocks when Partial mode.
    DIVC [1:0] Division Ratio
    0 0 fosc
    0 1 fosc / 2
    1 0 fosc / 4
    1 1 fosc / 8
    RTNC [4:0]: RTNC [4:0] is used to set 1H (line) period of Partial mode at MCU interface.
    RTNC [4:0]
    Clock per
    Line
    RTNC [4:0]
    Clock per
    Line
    RTNC [4:0]
    Clock per
    Line
    0 0 0 0 0 Setting prohibited 0 1 0 1 1 Setting prohibited 1 0 1 1 0 22 clocks
    0 0 0 0 1 Setting prohibited 0 1 1 0 0 Setting prohibited 1 0 1 1 1 23 clocks
    0 0 0 1 0 Setting prohibited 0 1 1 0 1 Setting prohibited 1 1 0 0 0 24 clocks
    0 0 0 1 1 Setting prohibited 0 1 1 1 0 Setting prohibited 1 1 0 0 1 25 clocks
    0 0 1 0 0 Setting prohibited 0 1 1 1 1 Setting prohibited 1 1 0 1 0 26 clocks
    0 0 1 0 1 Setting prohibited 1 0 0 0 0 16 clocks 1 1 0 1 1 27 clocks
    0 0 1 1 0 Setting prohibited 1 0 0 0 1 17 clocks 1 1 1 0 0 28 clocks
    0 0 1 1 1 Setting prohibited 1 0 0 1 0 18 clocks 1 1 1 0 1 29 clocks
    0 1 0 0 0 Setting prohibited 1 0 0 1 1 19 clocks 1 1 1 1 0 30 clocks
    0 1 0 0 1 Setting prohibited 1 0 1 0 0 20 clocks 1 1 1 1 1 31 clocks
    0 1 0 1 0 Setting prohibited 1 0 1 0 1 21 clocks
    a-Si TFT LCD Single Chip Driver
    240RGBx320 Resolution and 262K color ILI9341
    The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
    reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
    Page 160 of 239
    Restriction EXTC should be high to enable this command
    Register
    Availability
    Status Availability
    Normal Mode ON, Idle Mode OFF, Sleep OUT Yes
    Normal Mode ON, Idle Mode ON, Sleep OUT Yes
    Partial Mode ON, Idle Mode OFF, Sleep OUT Yes
    Partial Mode ON, Idle Mode ON, Sleep OUT Yes
    Sleep IN Yes
    Default
    Default Value
    Status
    DIVC [1:0] RTNC [4:0]
    Power ON Sequence 2’b00 5’h1Bh
    SW Reset 2’b00 5’h1Bh
    HW Reset 2’b00 5’h1Bh
    a-Si TFT LCD Single Chip Driver
    240RGBx320 Resolution and 262K color ILI9341
    The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
    reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
    Page 161 of 239
    8.3.5. Display Inversion Control (B4h)
    B4h INVTR (Display Inversion Control)
    D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
    Command 0 1 ↑ XX 1 0 1 1 0 1 0 0 B4h
    1
    st Parameter 1 1 ↑ XX 0 0 0 0 0 NLA NLB NLC 02
    Description
    Display inversion mode set
    NLA: Inversion setting in full colors normal mode (Normal mode on)
    NLB: Inversion setting in Idle mode (Idle mode on)
    NLC: Inversion setting in full colors partial mode (Partial mode on / Idle mode off)
    NLA / NLB / NLC Inversion
    0 Line inversion
    1 Frame inversion
    Restriction EXTC should be high to enable this command
    Register
    Availability
    Status Availability
    Normal Mode ON, Idle Mode OFF, Sleep OUT Yes
    Normal Mode ON, Idle Mode ON, Sleep OUT Yes
    Partial Mode ON, Idle Mode OFF, Sleep OUT Yes
    Partial Mode ON, Idle Mode ON, Sleep OUT Yes
    Sleep IN Yes
    Default
    Default Value
    Status
    NLA NLB NLC
    Power ON Sequence 1’b0 1’b1 1’b0
    SW Reset 1’b0 1’b1 1’b0
    H/W Reset 1’b0 1’b1 1’b0
    a-Si TFT LCD Single Chip Driver
    240RGBx320 Resolution and 262K color ILI9341
    The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
    reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
    Page 162 of 239
    8.3.6. Blanking Porch Control (B5h)
    B5h PRCTR (Blanking Porch)
    D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
    Command 0 1 ↑ XX 1 0 1 1 0 1 0 1 B5h
    1
    stParameter 1 1 ↑ XX 0 VFP [6:0] 02
    2
    ndParameter 1 1 ↑ XX 0 VBP [6:0] 02
    3
    rdParameter 1 1 ↑ XX 0 0 0 HFP [4:0] 0A
    4
    thParameter 1 1 ↑ XX 0 0 0 HBP [4:0] 14
    Description
    VFP [6:0] / VBP [6:0]: The VFP [6:0] and VBP [6:0] bits specify the line number of vertical front and back porch period
    respectively.
    VFP [6:0]
    VBP [6:0]
    Number of HSYNC of front/back porch
    VFP [6:0]
    VBP [6:0]
    Number of HSYNC of front/back porch
    0000000 Setting inhibited 1000000 64
    0000001 Setting inhibited 1000001 65
    0000010 2 1000010 66
    0000011 3 1000011 67
    0000100 4 1000100 68
    0000101 5 1000101 69
    0000110 6 1000110 70
    0000111 7 1000111 71
    0001000 8 1001000 72
    0001001 9 1001001 73
    0001010 10 1001010 74
    0001011 11 1001011 75
    0001100 12 1001100 76
    0001101 13 1001101 77
    :
    :
    :
    :
    :
    :
    :
    :
    0111101 61 1111101 125
    0111110 62 1111110 126
    0111111 63 1111111 127
    Note: VFP + VBP 254 HSYNC signals ≦
    HFP [4:0] / HBP [4:0]: The HFP [4:0] and HBP [4:0] bits specify the line number of horizontal front and back porch period
    respectively.
    HFP [4:0]
    HBP [4:0]
    Number of DOTCLK of the front/back porch
    HFP [4:0]
    HBP [4:0]
    Number of DOTCLK of front/back porch
    00000 Setting prohibited 10000 16
    00001 Setting prohibited 10001 17
    00010 2 10010 18
    00011 3 10011 19
    00100 4 10100 20
    00101 5 10101 21
    00110 6 10110 22
    00111 7 10111 23
    01000 8 11000 24
    01001 9 11001 25
    01010 10 11010 26
    01011 11 11011 27
    01100 12 11100 28
    01101 13 11101 29
    01110 14 11110 30
    01111 15 11111 31
    a-Si TFT LCD Single Chip Driver
    240RGBx320 Resolution and 262K color ILI9341
    The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
    reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
    Page 163 of 239
    Restriction EXTC should be high to enable this command
    Register
    Availability
    Status Availability
    Normal Mode ON, Idle Mode OFF, Sleep OUT Yes
    Normal Mode ON, Idle Mode ON, Sleep OUT Yes
    Partial Mode ON, Idle Mode OFF, Sleep OUT Yes
    Partial Mode ON, Idle Mode ON, Sleep OUT Yes
    Sleep IN Yes
    Default
    Default Value
    Status
    VFP [6:0] VBP [6:0] HFP [4:0] HBP [4:0]
    Power ON Sequence 7’h02h 7’h02h 5’h0Ah 5’h14h
    SW Reset 7’h02h 7’h02h 5’h0Ah 5’h14h
    HW Reset 7’h02h 7’h02h 5’h0Ah 5’h14h
    a-Si TFT LCD Single Chip Driver
    240RGBx320 Resolution and 262K color ILI9341
    The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
    reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
    Page 164 of 239
    8.3.7. Display Function Control (B6h)
    B6h DISCTRL (Display Function Control)
    D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
    Command 0 1 ↑ XX 1 0 1 1 0 1 1 0 B6h
    1
    st Parameter 1 1 ↑ XX 0 0 0 0 PTG [1:0] PT [1:0] 0A
    2
    nd Parameter 1 1 ↑ XX REV GS SS SM ISC [3:0] 82
    3
    rd Parameter 1 1 ↑ XX 0 0 NL [5:0] 27
    4
    th Parameter 1 1 ↑ XX 0 0 PCDIV [5:0] XX
    Description
    PTG [1:0]: Set the scan mode in non-display area.
    PTG1 PTG0 Gate outputs in non-display area Source outputs in non-display area VCOM output
    0 0 Normal scan Set with the PT [2:0] bits VCOMH/VCOML
    0 1 Setting prohibited --- ---
    1 0 Interval scan Set with the PT [2:0] bits
    1 1 Setting prohibited --- ---
    PT [1:0]: Determine source/VCOM output in a non-display area in the partial display mode.
    Source output on non-display area VCOM output on non-display area
    PT [1:0]
    Positive polarity Negative polarity Positive polarity Negative polarity
    0 0 V63 V0 VCOML VCOMH
    0 1 V0 V63 VCOML VCOMH
    1 0 AGND AGND AGND AGND
    1 1 Hi-Z Hi-Z AGND AGND
    SS: Select the shift direction of outputs from the source driver.
    SS Source Output Scan Direction
    0 S1  S720
    1 S720  S1
    In addition to the shift direction, the settings for both SS and BGR bits are required to change the assignment of R, G,
    and B dots to the source driver pins.
    To assign R, G, B dots to the source driver pins from S1 to S720, set SS = 0.
    To assign R, G, B dots to the source driver pins from S720 to S1, set SS = 1.
    REV: Select whether the liquid crystal type is normally white type or normally black type.
    REV Liquid crystal type
    0 Normally black
    1 Normally white
    ISC [3:0]: Specify the scan cycle interval of gate driver in non-display area when PTG [1:0] =”10” to select interval scan.
    Then scan cycle is set as odd number from 0~29 frame periods. The polarity is inverted every scan cycle.
    ISC [3:0] Scan Cycle fFLM = 60Hz
    0000 1 frame 17ms
    0001 3 frames 51ms
    0010 5 frames 85ms
    0011 7 frames 119ms
    0100 9 frames 153ms
    0101 11 frames 187ms
    0110 13 frames 221ms
    0111 15 frames 255ms
    a-Si TFT LCD Single Chip Driver
    240RGBx320 Resolution and 262K color ILI9341
    The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
    reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
    Page 165 of 239
    1000 17 frames 289ms
    1001 19 frames 323ms
    1010 21 frames 357ms
    1011 23 frames 391ms
    1100 25 frames 425ms
    1101 27 frames 459ms
    1110 29 frames 493ms
    1111 31 frames 527ms
    GS: Sets the direction of scan by the gate driver in the range determined by SCN [4:0] and NL [4:0]. The scan direction
    determined by GS = 0 can be reversed by setting GS = 1.
    GS Gate Output Scan Direction
    0 G1  G320
    1 G320  G1
    SM: Sets the gate driver pin arrangement in combination with the GS bit to select the optimal scan mode for the module.
    SM GS Scan Direction Gate Output Sequence
    0 0
    G2 to G320
    G1 to G319
    G1G2G3G4 ………………
    ….G317G318G319G320
    0 1
    G2 to G320
    G1 to G319
    G320G319->G318G317……
    …. G4G3G2G1
    a-Si TFT LCD Single Chip Driver
    240RGBx320 Resolution and 262K color ILI9341
    The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
    reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
    Page 166 of 239
    1 0
    G2 to G320
    G1 to G319
    G1G3………...G317G319
    G2G4…………G318G320
    1 1
    G2 to G320
    G1 to G319
    G320G318………...G4G2
    G319G317…………G3G1
    NL [5:0]: Sets the number of lines to drive the LCD at an interval of 8 lines. The GRAM address mapping is not affected
    by the number of lines set by NL [5:0]. The number of lines must be the same or more than the number of lines necessary
    for the size of the liquid crystal panel.
    NL [5:0] LCD Drive Line NL [5:0] LCD Driver Line
    0 0 0 0 0 0 Setting prohibited 0 1 0 1 0 1 176 lines
    0 0 0 0 0 1 16 lines 0 1 0 1 1 0 184 lines
    0 0 0 0 1 0 24 lines 0 1 0 1 1 1 192 lines
    0 0 0 0 1 1 32 lines 0 1 1 0 0 0 200 lines
    0 0 0 1 0 0 40 lines 0 1 1 0 0 1 208 lines
    0 0 0 1 0 1 48 lines 0 1 1 0 1 0 216 lines
    0 0 0 1 1 0 56 lines 0 1 1 0 1 1 224 lines
    0 0 0 1 1 1 64 lines 0 1 1 1 0 0 232 lines
    0 0 1 0 0 0 72 lines 0 1 1 1 0 1 240 lines
    0 0 1 0 0 1 80 lines 0 1 1 1 1 0 248 lines
    0 0 1 0 1 0 88 lines 0 1 1 1 1 1 256 lines
    0 0 1 0 1 1 96 lines 1 0 0 0 0 0 264 lines
    0 0 1 1 0 0 104 lines 1 0 0 0 0 1 272 lines
    0 0 1 1 0 1 112 lines 1 0 0 0 1 0 280 lines
    0 0 1 1 1 0 120 lines 1 0 0 0 1 1 288 lines
    0 0 1 1 1 1 128 lines 1 0 0 1 0 0 296 lines
    0 1 0 0 0 0 136 lines 1 0 0 1 0 1 304 lines
    0 1 0 0 0 1 144 lines 1 0 0 1 1 0 312 lines
    0 1 0 0 1 0 152 lines 1 0 0 1 1 1 320 lines
    0 1 0 0 1 1 160 lines Others Setting inhibited
    0 1 0 1 0 0 168 lines
    PCDIV [5:0]:
    a-Si TFT LCD Single Chip Driver
    240RGBx320 Resolution and 262K color ILI9341
    The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
    reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
    Page 167 of 239
    external fosc=
    2 (PCDIV 1)
    DOTCLK
    × +
    Restriction EXTC should be high to enable this command
    Register
    Availability
    Status Availability
    Normal Mode ON, Idle Mode OFF, Sleep OUT Yes
    Normal Mode ON, Idle Mode ON, Sleep OUT Yes
    Partial Mode ON, Idle Mode OFF, Sleep OUT Yes
    Partial Mode ON, Idle Mode ON, Sleep OUT Yes
    Sleep IN Yes
    Default
    Default Value
    Status
    PTG [1:0] PT [1:0] REV GS SS SM ISC [3:0] NL [5:0]
    Power ON Sequence 2’b10 2’b10 1’b1 1’b0 1’b0 1’b0 4’b0010 6’h27h
    SW Reset 2’b10 2’b10 1’b1 1’b0 1’b0 1’b0 4’b0010 6’h27h
    HW Reset 2’b10 2’b10 1’b1 1’b0 1’b0 1’b0 4’b0010 6’h27h
    a-Si TFT LCD Single Chip Driver
    240RGBx320 Resolution and 262K color ILI9341
    The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
    reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
    Page 168 of 239
    8.3.8. Entry Mode Set (B7h)
    B7h ETMOD (Entry Mode Set)
    D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
    Command 0 1 ↑ XX 1 0 1 1 0 1 1 1 B7h
    Parameter 1 1 ↑ XX 0 0 0 0 0 GON DTE GAS 06
    Description
    GAS: Low voltage detection control.
    GAS Low voltage detection
    0 Enable
    1 Disable
    GON/DTE: Set the output level of gate driver G1 ~ G320 as follows
    GON DTE G1~G320 Gate Output
    0 0 VGH
    0 1 VGH
    1 0 VGL
    1 1 Normal display
    Restriction EXTC should be high to enable this command
    Register
    Availability
    Status Availability
    Normal Mode ON, Idle Mode OFF, Sleep OUT Yes
    Normal Mode ON, Idle Mode ON, Sleep OUT Yes
    Partial Mode ON, Idle Mode OFF, Sleep OUT Yes
    Partial Mode ON, Idle Mode ON, Sleep OUT Yes
    Sleep IN Yes
    Default
    Default Value
    Status
    GON DTE GAS
    Power ON Sequence 1’b1 1’b1 1’b0
    SW Reset 1’b1 1’b1 1’b0
    HW Reset 1’b1 1’b1 1’b0
    a-Si TFT LCD Single Chip Driver
    240RGBx320 Resolution and 262K color ILI9341
    The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
    reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
    Page 169 of 239
    8.3.9. Backlight Control 1 (B8h)
    B8h Backlight Control 1
    D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
    Command 0 1 ↑ XX 1 0 1 1 1 0 0 0 B8h
    Parameter 1 ↑ XX 0 0 0 0 TH*UI [3] TH_UI [2] TH_UI [1] TH_UI [0] 0C
    Description
    TH_UI [3:0]: These bits are used to set the percentage of grayscale data accumulate histogram value in the user interface
    (UI) mode. This ratio of maximum number of pixels that makes display image white (=data “255”) to the total of
    pixels by image processing.
    TH_UI [3:0] Description TH_UI [3:0] Description
    4’0h 99% 4’8h 84%
    4’1h 98% 4’9h 82%
    4’2h 96% 4’Ah 80%
    4’3h 94% 4’Bh 78%
    4’4h 92% 4’Ch 76%
    4’5h 90% 4’Dh 74%
    4’6h 88% 4’Eh 72%
    4’7h 86% 4’Fh 70%
    Register
    Availability
    Status Availability
    Normal Mode On, Idle Mode Off, Sleep Out Yes
    Normal Mode On, Idle Mode On, Sleep Out Yes
    Partial Mode On, Idle Mode Off, Sleep Out Yes
    Partial Mode On, Idle Mode On, Sleep Out Yes
    Sleep In Yes
    Default
    Default Value
    Status
    TH_UI [3:0]
    Power On Sequence 4’b0110
    SW Reset No change
    HW Reset 4’b0110
    a-Si TFT LCD Single Chip Driver
    240RGBx320 Resolution and 262K color ILI9341
    The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
    reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
    Page 170 of 239
    8.3.10. Backlight Control 2 (B9h)
    B9h Backlight Control 2
    D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
    Command 0 1 ↑ XX 1 0 1 1 1 0 0 1 B9h
    Parameter 1 1 ↑ XX TH_MV
    [3]
    TH_MV
    [2]
    TH_MV
    [1]
    TH_MV
    [0]
    TH_ST
    [3]
    TH_ST
    [2]
    TH_ST
    [1]
    TH_ST
    [0] CC
    Description
    TH_ST [3:0]: These bits are used to set the percentage of grayscale data accumulate histogram value in the still picture
    mode. This ratio of maximum number of pixels that makes display image white (=data “255”) to the total of pixels
    by image processing.
    TH_ST [3:0] Description TH_ST [3:0] Description
    4’0h 99% 4’8h 84%
    4’1h 98% 4’9h 82%
    4’2h 96% 4’Ah 80%
    4’3h 94% 4’Bh 78%
    4’4h 92% 4’Ch 76%
    4’5h 90% 4’Dh 74%
    4’6h 88% 4’Eh 72%
    4’7h 86% 4’Fh 70%
    TH_MV [3:0]: These bits are used to set the percentage of grayscale data accumulate histogram value in the moving image
    mode. This ratio of maximum number of pixels that makes display image white (=data “255”) to the total of pixels
    by image processing.
    TH_MV [3:0] Description TH_MV [3:0] Description
    4’0h 99% 4’8h 84%
    4’1h 98% 4’9h 82%
    4’2h 96% 4’Ah 80%
    4’3h 94% 4’Bh 78%
    4’4h 92% 4’Ch 76%
    4’5h 90% 4’Dh 74%
    4’6h 88% 4’Eh 72%
    4’7h 86% 4’Fh 70%
    100%
    Histogram
    TH_MV[3:0]
    TH_ST[3:0]
    TH_UI[3:0]
    Dth 255
    Gray Scales
    a-Si TFT LCD Single Chip Driver
    240RGBx320 Resolution and 262K color ILI9341
    The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
    reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
    Page 171 of 239
    Register
    Availability
    Status Availability
    Normal Mode On, Idle Mode Off, Sleep Out Yes
    Normal Mode On, Idle Mode On, Sleep Out Yes
    Partial Mode On, Idle Mode Off, Sleep Out Yes
    Partial Mode On, Idle Mode On, Sleep Out Yes
    Sleep In Yes
    Default
    Default Value
    Status
    TH_MV [3:0] TH_ST [3:0]
    Power On Sequence 4’b1100 4’b1100
    SW Reset No change No change
    HW Reset 4’b1100 4’b1100
    a-Si TFT LCD Single Chip Driver
    240RGBx320 Resolution and 262K color ILI9341
    The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
    reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
    Page 172 of 239
    8.3.11. Backlight Control 3 (BAh)
    BAh Backlight Control 3
    D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
    Command 0 1 ↑ XX 1 0 1 1 1 0 1 0 BAh
    Parameter 1 1 ↑ XX 0 0 0 0
    DTH_UI
    [3]
    DTH_UI
    [2]
    DTH_UI
    [1]
    DTH_UI
    [0] 04
    Description
    DTH_UI [3:0]: This parameter is used set the minimum limitation of grayscale threshold value in User Icon (UI) image mode.
    This register setting will limit the minimum Dth value to prevent the display image from being too white and
    the display quality is not acceptable.
    DTH_UI [3:0] Description DTH_UI [3:0] Description
    4’0h 252 4’8h 220
    4’1h 248 4’9h 216
    4’2h 244 4’Ah 212
    4’3h 240 4’Bh 208
    4’4h 236 4’Ch 204
    4’5h 232 4’Dh 200
    4’6h 228 4’Eh 196
    4’7h 224 4’Fh 192
    Register
    Availability
    Status Availability
    Normal Mode On, Idle Mode Off, Sleep Out Yes
    Normal Mode On, Idle Mode On, Sleep Out Yes
    Partial Mode On, Idle Mode Off, Sleep Out Yes
    Partial Mode On, Idle Mode On, Sleep Out Yes
    Sleep In Yes
    Default
    Default Value
    Status
    DTH_UI [3:0]
    Power On Sequence 4’b0100
    SW Reset No change
    HW Reset 4’b0100
    a-Si TFT LCD Single Chip Driver
    240RGBx320 Resolution and 262K color ILI9341
    The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
    reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
    Page 173 of 239
    8.3.12. Backlight Control 4 (BBh)
    BBh Backlight Control 4
    D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
    Command 0 1 ↑ XX 1 0 1 1 1 0 1 1 BBh
    Parameter 1 1 ↑ XX DTH_MV
    [3]
    DTH_MV
    [2]
    DTH_MV
    [1]
    DTH_MV
    [0]
    DTH_ST
    [3]
    DTH_ST
    [2]
    DTH_ST
    [1]
    DTH_ST
    [0] 65
    Description
    DTH_ST [3:0]/DTH_MV [3:0]: This parameter is used set the minimum limitation of grayscale threshold value. This register
    setting will limit the minimum Dth value to prevent the display image from being too white and the
    display quality is not acceptable.
    DTH_ST [3:0] Description DTH_ST [3:0] Description
    4’0h 224 4’8h 192
    4’1h 220 4’9h 188
    4’2h 216 4’Ah 184
    4’3h 212 4’Bh 180
    4’4h 208 4’Ch 176
    4’5h 204 4’Dh 172
    4’6h 200 4’Eh 168
    4’7h 196 4’Fh 164
    DTH_MV [3:0] Description DTH_MV [3:0] Description
    4’0h 224 4’8h 192
    4’1h 220 4’9h 188
    4’2h 216 4’Ah 184
    4’3h 212 4’Bh 180
    4’4h 208 4’Ch 176
    4’5h 204 4’Dh 172
    4’6h 200 4’Eh 168
    4’7h 196 4’Fh 164
    Transmittance
    DTH 255
    Gray Scales
    Register
    Availability
    Status Availability
    Normal Mode On, Idle Mode Off, Sleep Out Yes
    Normal Mode On, Idle Mode On, Sleep Out Yes
    Partial Mode On, Idle Mode Off, Sleep Out Yes
    Partial Mode On, Idle Mode On, Sleep Out Yes
    Sleep In Yes
    a-Si TFT LCD Single Chip Driver
    240RGBx320 Resolution and 262K color ILI9341
    The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
    reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
    Page 174 of 239
    Default
    Default Value
    Status
    DTH_MV [3:0] DTH_ST [3:0]
    Power On Sequence 4’b0110 4’b0101
    SW Reset No change No change
    HW Reset 4’b0110 4’b0101
    a-Si TFT LCD Single Chip Driver
    240RGBx320 Resolution and 262K color ILI9341
    The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
    reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
    Page 175 of 239
    8.3.13. Backlight Control 5 (BCh)
    BCh Backlight Control 5
    D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
    Command 0 1 ↑ XX 1 0 1 1 1 1 0 0 BCh
    Parameter 1 1 ↑ XX DIM2 [3] DIM2 [2] DIM2 [1] DIM2 [0] 0 DIM1 [2] DIM1 [1] DIM1 [0] 44
    Description
    DIM1 [2:0]: This parameter is used to set the transition time of brightness level to avoid the sharp brightness transition on
    vision.
    DIM1 [2:0] Description
    3’0h 1 frame
    3’1h 1 frame
    3’2h 2 frames
    3’3h 4 frames
    3’4h 8 frames
    3’5h 16 frames
    3’6h 32 frames
    3’7h 64 frames
    Time
    DIM1[2:0] DIM1[2:0]
    Brightness =A
    Brightness =B
    Brightness =C
    Transition
    time
    Transition
    time
    DIM2[2:0]
    DIM2 [3:0]: This parameter is used to set the threshold of brightness change.
    When the brightness transition difference is smaller than DIM2 [3:0], the brightness transition will be ignored.
    For example:
    If | brightness B – brightness A| < DIM2 [2:0], the brightness transition will be ignored and keep the brightness A.
    Register
    Availability
    Status Availability
    Normal Mode On, Idle Mode Off, Sleep Out Yes
    Normal Mode On, Idle Mode On, Sleep Out Yes
    Partial Mode On, Idle Mode Off, Sleep Out Yes
    Partial Mode On, Idle Mode On, Sleep Out Yes
    Sleep In Yes
    Default
    Default Value
    Status
    DIM2 [3:0] DIM1 [2:0]
    Power On Sequence 4’b0100 4’b0100
    SW Reset No change No change
    HW Reset 4’b0100 4’b0100
    a-Si TFT LCD Single Chip Driver
    240RGBx320 Resolution and 262K color ILI9341
    The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
    reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
    Page 176 of 239
    8.3.14. Backlight Control 7 (BEh)
    BEh Backlight Control 7
    D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
    Command 0 1 ↑ XX 1 0 1 1 1 1 1 0 BEh
    Parameter 1 1 ↑ XX PWM*
    DIV[7]
    PWM*
    DIV[6]
    PWM*
    DIV[5]
    PWM*
    DIV[4]
    PWM*
    DIV[3]
    PWM*
    DIV[2]
    PWM*
    DIV[1]
    PWM\_
    DIV[0] 0F
    Description
    PWM_DIV [7:0]: PWM_OUT output frequency control. This command is used to adjust the PWM waveform frequency of
    PWM_OUT. The PWM frequency can be calculated by using the following equation.
    fPWM_OUT =
    (PWM_DIV ]0:7[ )1 255
    16MHz
- ×
  PWM_DIV [7:0] fPWM_OUT
  8’h0 62.74 KHz
  8’h1 31.38 KHz
  8’h2 20.915KHz
  8’h3 15.686KHz
  8’h4 12.549 KHz
  … …
  8’hFB 249Hz
  8’hFC 248Hz
  8’hFD 247Hz
  8’hFE 246Hz
  8’hFF 245Hz
  PWM_OUT
  fPWM_OUT
  tON tOFF
  Note: The output frequency tolerance of internal frequency divider in CABC is ±10%
  Register
  Availability
  Status Availability
  Normal Mode On, Idle Mode Off, Sleep Out Yes
  Normal Mode On, Idle Mode On, Sleep Out Yes
  Partial Mode On, Idle Mode Off, Sleep Out Yes
  Partial Mode On, Idle Mode On, Sleep Out Yes
  Sleep In Yes
  Default
  Status Default Value
  Power On Sequence PWM_DIV [7:0]=0Fh
  SW Reset No change
  HW Reset PWM_DIV [7:0]=0Fh
  a-Si TFT LCD Single Chip Driver
  240RGBx320 Resolution and 262K color ILI9341
  The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
  reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
  Page 177 of 239
  8.3.15. Backlight Control 8 (BFh)
  BFh Backlight Control 2
  D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
  Command 0 1 ↑ XX 1 0 1 1 1 1 1 1 BFh
  Parameter 1 1 ↑ XX 0 0 0 0 0 LEDONR LEDONPOL LEDPWMPOL 00
  Description
  LEDPWMPOL: The bit is used to define polarity of LEDPWM signal.
  BL LEDPWMPOL LEDPWM pin
  0 0 0
  0 1 1
  1 0 Original polarity of PWM signal
  1 1 Inversed polarity of PWM signal
  LEDONPOL: This bit is used to control LEDON pin.
  BL LEDONPOL LEDON pin
  0 0 0
  0 1 1
  1 0 LEDONR
  1 1 Inversed LEDONR

LEDONR: This bit is used to control LEDON pin.
LEDONR Description
0 Low
1 High
Register
Availability
Status Availability
Normal Mode On, Idle Mode Off, Sleep Out Yes
Normal Mode On, Idle Mode On, Sleep Out Yes
Partial Mode On, Idle Mode Off, Sleep Out Yes
Partial Mode On, Idle Mode On, Sleep Out Yes
Sleep In Yes
Default
Default Value
Status
LEDONR LEDONPOL LEDPWMPOL
Power On Sequence 1’b0 1’b0 1’b0
SW Reset No change No change No change
HW Reset 1’b0 1’b0 1’b0
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 178 of 239
8.3.16. Power Control 1 (C0h)
C0h PWCTRL 1 (Power Control 1)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 1 1 0 0 0 0 0 0 C0h
1
stParameter 1 1 ↑ XX 0 0 VRH [5:0] 21
Description
VRH [5:0]: Set the GVDD level, which is a reference level for the VCOM level and the grayscale voltage level.
VRH [5:0] GVDD VRH [5:0] GVDD
0 0 0 0 0 0 Setting prohibited 1 0 0 0 0 0 4.45 V
0 0 0 0 0 1 Setting prohibited 1 0 0 0 0 1 4.50 V
0 0 0 0 1 0 Setting prohibited 1 0 0 0 1 0 4.55 V
0 0 0 0 1 1 3.00 V 1 0 0 0 1 1 4.60 V
0 0 0 1 0 0 3.05 V 1 0 0 1 0 0 4.65 V
0 0 0 1 0 1 3.10 V 1 0 0 1 0 1 4.70 V
0 0 0 1 1 0 3.15 V 1 0 0 1 1 0 4.75 V
0 0 0 1 1 1 3.20 V 1 0 0 1 1 1 4.80 V
0 0 1 0 0 0 3.25 V 1 0 1 0 0 0 4.85 V
0 0 1 0 0 1 3.30 V 1 0 1 0 0 1 4.90 V
0 0 1 0 1 0 3.35 V 1 0 1 0 1 0 4.95 V
0 0 1 0 1 1 3.40 V 1 0 1 0 1 1 5.00 V
0 0 1 1 0 0 3.45 V 1 0 1 1 0 0 5.05 V
0 0 1 1 0 1 3.50 V 1 0 1 1 0 1 5.10 V
0 0 1 1 1 0 3.55 V 1 0 1 1 1 0 5.15 V
0 0 1 1 1 1 3.60 V 1 0 1 1 1 1 5.20 V
0 1 0 0 0 0 3.65 V 1 1 0 0 0 0 5.25 V
0 1 0 0 0 1 3.70 V 1 1 0 0 0 1 5.30 V
0 1 0 0 1 0 3.75 V 1 1 0 0 1 0 5.35 V
0 1 0 0 1 1 3.80 V 1 1 0 0 1 1 5.40 V
0 1 0 1 0 0 3.85 V 1 1 0 1 0 0 5.45 V
0 1 0 1 0 1 3.90 V 1 1 0 1 0 1 5.50 V
0 1 0 1 1 0 3.95 V 1 1 0 1 1 0 5.55 V
0 1 0 1 1 1 4.00 V 1 1 0 1 1 1 5.60 V
0 1 1 0 0 0 4.05 V 1 1 1 0 0 0 5.65 V
0 1 1 0 0 1 4.10 V 1 1 1 0 0 1 5.70 V
0 1 1 0 1 0 4.15 V 1 1 1 0 1 0 5.75 V
0 1 1 0 1 1 4.20 V 1 1 1 0 1 1 5.80 V
0 1 1 1 0 0 4.25 V 1 1 1 1 0 0 5.85 V
0 1 1 1 0 1 4.30 V 1 1 1 1 0 1 5.90 V
0 1 1 1 1 0 4.35 V 1 1 1 1 1 0 5.95 V
0 1 1 1 1 1 4.40 V 1 1 1 1 1 1 6.00 V
Note1: Make sure that VC and VRH setting restriction: GVDD ≦ (AVDD - 0.5) V.
Restriction EXTC should be high to enable this command
Register
Availability
Status Availability
Normal Mode ON, Idle Mode OFF, Sleep OUT Yes
Normal Mode ON, Idle Mode ON, Sleep OUT Yes
Partial Mode ON, Idle Mode OFF, Sleep OUT Yes
Partial Mode ON, Idle Mode ON, Sleep OUT Yes
Sleep IN Yes
Default
Default Value
Status
VRH [5:0]
Power ON Sequence 6’h21h
SW Reset 6’h21h
HW Reset 6’h21h
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 179 of 239
8.3.17. Power Control 2 (C1h)
C1h PWCTRL 2 (Power Control 2)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 1 1 0 0 0 0 0 1 C1h
Parameter 1 1 ↑ XX 0 0 0 1 0 BT [2:0] 10
Description
BT [2:0]: Sets the factor used in the step-up circuits.
Select the optimal step-up factor for the operating voltage. To reduce power consumption, set a smaller factor.
BT [2:0] AVDD VGH VGL
0 0 0 -VCI x 4
0 0 1
VCI x 7
-VCI x 3
0 1 0 -VCI x 4
0 1 1
VCI x 2
VCI x 6
-VCI x 3
Note1: Make sure that AVDD setting restriction: AVDD ≦ 5.5 V.
2: Make sure that VGH and VGL setting restriction: VGH -VGL 32 ≦ V.
Restriction EXTC should be high to enable this command
Register
Availability
Status Availability
Normal Mode ON, Idle Mode OFF, Sleep OUT Yes
Normal Mode ON, Idle Mode ON, Sleep OUT Yes
Partial Mode ON, Idle Mode OFF, Sleep OUT Yes
Partial Mode ON, Idle Mode ON, Sleep OUT Yes
Sleep IN Yes
Default
Default Value
Status
BT [2:0]
Power ON Sequence 3’b000
SW Reset 3’b000
HW Reset 3’b000
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 180 of 239
8.3.18. VCOM Control 1(C5h)
C5h VMCTRL1 (VCOM Control 1)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 1 1 0 0 0 1 0 1 C5h
1
st Parameter 1 1 ↑ XX 0 VMH [6:0] 31
2
ndParameter 1 1 ↑ XX 0 VML [6:0] 3C
Description
VMH [6:0] : Set the VCOMH voltage.
VMH [6:0] VCOMH(V) VMH [6:0] VCOMH(V) VMH [6:0] VCOMH(V) VMH [6:0] VCOMH(V)
0000000 2.700 0100000 3.500 1000000 4.300 1100000 5.100
0000001 2.725 0100001 3.525 1000001 4.325 1100001 5.125
0000010 2.750 0100010 3.550 1000010 4.350 1100010 5.150
0000011 2.775 0100011 3.575 1000011 4.375 1100011 5.175
0000100 2.800 0100100 3.600 1000100 4.400 1100100 5.200
0000101 2.825 0100101 3.625 1000101 4.425 1100101 5.225
0000110 2.850 0100110 3.650 1000110 4.450 1100110 5.250
0000111 2.875 0100111 3.675 1000111 4.475 1100111 5.275
0001000 2.900 0101000 3.700 1001000 4.500 1101000 5.300
0001001 2.925 0101001 3.725 1001001 4.525 1101001 5.325
0001010 2.950 0101010 3.750 1001010 4.550 1101010 5.350
0001011 2.975 0101011 3.775 1001011 4.575 1101011 5.375
0001100 3.000 0101100 3.800 1001100 4.600 1101100 5.400
0001101 3.025 0101101 3.825 1001101 4.625 1101101 5.425
0001110 3.050 0101110 3.850 1001110 4.650 1101110 5.450
0001111 3.075 0101111 3.875 1001111 4.675 1101111 5.475
0010000 3.100 0110000 3.900 1010000 4.700 1110000 5.500
0010001 3.125 0110001 3.925 1010001 4.725 1110001 5.525
0010010 3.150 0110010 3.950 1010010 4.750 1110010 5.550
0010011 3.175 0110011 3.975 1010011 4.775 1110011 5.575
0010100 3.200 0110100 4.000 1010100 4.800 1110100 5.600
0010101 3.225 0110101 4.025 1010101 4.825 1110101 5.625
0010110 3.250 0110110 4.050 1010110 4.850 1110110 5.650
0010111 3.275 0110111 4.075 1010111 4.875 1110111 5.675
0011000 3.300 0111000 4.100 1011000 4.900 1111000 5.700
0011001 3.325 0111001 4.125 1011001 4.925 1111001 5.725
0011010 3.350 0111010 4.150 1011010 4.950 1111010 5.750
0011011 3.375 0111011 4.175 1011011 4.975 1111011 5.775
0011100 3.400 0111100 4.200 1011100 5.000 1111100 5.800
0011101 3.425 0111101 4.225 1011101 5.025 1111101 5.825
0011110 3.450 0111110 4.250 1011110 5.050 1111110 5.850
0011111 3.475 0111111 4.275 1011111 5.075 1111111 5.875
VML [6:0] : Set the VCOML voltage
VML [6:0] VCOML(V) VML [6:0] VCOML(V) VML [6:0] VCOML(V) VML [6:0] VCOML(V)
0000000 -2.500 0100000 -1.700 1000000 -0.900 1100000 -0.100
0000001 -2.475 0100001 -1.675 1000001 -0.875 1100001 -0.075
0000010 -2.450 0100010 -1.650 1000010 -0.850 1100010 -0.050
0000011 -2.425 0100011 -1.625 1000011 -0.825 1100011 -0.025
0000100 -2.400 0100100 -1.600 1000100 -0.800 1100100 0
0000101 -2.375 0100101 -1.575 1000101 -0.775 1100101 Reserved
0000110 -2.350 0100110 -1.550 1000110 -0.750 1100110 Reserved
0000111 -2.325 0100111 -1.525 1000111 -0.725 1100111 Reserved
0001000 -2.300 0101000 -1.500 1001000 -0.700 1101000 Reserved
0001001 -2.275 0101001 -1.475 1001001 -0.675 1101001 Reserved
0001010 -2.250 0101010 -1.450 1001010 -0.650 1101010 Reserved
0001011 -2.225 0101011 -1.425 1001011 -0.625 1101011 Reserved
0001100 -2.200 0101100 -1.400 1001100 -0.600 1101100 Reserved
0001101 -2.175 0101101 -1.375 1001101 -0.575 1101101 Reserved
0001110 -2.150 0101110 -1.350 1001110 -0.550 1101110 Reserved
0001111 -2.125 0101111 -1.325 1001111 -0.525 1101111 Reserved
0010000 -2.100 0110000 -1.300 1010000 -0.500 1110000 Reserved
0010001 -2.075 0110001 -1.275 1010001 -0.475 1110001 Reserved
0010010 -2.050 0110010 -1.250 1010010 -0.450 1110010 Reserved
0010011 -2.025 0110011 -1.225 1010011 -0.425 1110011 Reserved
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 181 of 239
0010100 -2.000 0110100 -1.200 1010100 -0.400 1110100 Reserved
0010101 -1.975 0110101 -1.175 1010101 -0.375 1110101 Reserved
0010110 -1.950 0110110 -1.150 1010110 -0.350 1110110 Reserved
0010111 -1.925 0110111 -1.125 1010111 -0.325 1110111 Reserved
0011000 -1.900 0111000 -1.100 1011000 -0.300 1111000 Reserved
0011001 -1.875 0111001 -1.075 1011001 -0.275 1111001 Reserved
0011010 -1.850 0111010 -1.050 1011010 -0.250 1111010 Reserved
0011011 -1.825 0111011 -1.025 1011011 -0.225 1111011 Reserved
0011100 -1.800 0111100 -1.000 1011100 -0.200 1111100 Reserved
0011101 -1.775 0111101 -0.975 1011101 -0.175 1111101 Reserved
0011110 -1.750 0111110 -0.950 1011110 -0.150 1111110 Reserved
0011111 -1.725 0111111 -0.925 1011111 -0.125 1111111 Reserved
Restriction EXTC should be high to enable this command
Register
Availability
Status Availability
Normal Mode ON, Idle Mode OFF, Sleep OUT Yes
Normal Mode ON, Idle Mode ON, Sleep OUT Yes
Partial Mode ON, Idle Mode OFF, Sleep OUT Yes
Partial Mode ON, Idle Mode ON, Sleep OUT Yes
Sleep IN Yes
Default
Default Value
Status
VMH [6:0] VML [6:0]
Power ON Sequence 7’h31 7’h3C
SW Reset 7’h31 7’h3C
HW Rest 7’h31 7’h3C
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 182 of 239
8.3.19. VCOM Control 2(C7h)
C7h VMCTRL1 (VCOM Control 1)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 1 1 0 0 0 1 1 1 C7h
Parameter 1 1 ↑ XX nVM VMF [6:0] C0
Description
nVM: nVM equals to “0” after power on reset and VCOM offset equals to program MTP value. When nVM set to “1”, setting
of VMF [6:0] becomes valid and VCOMH/VCOML can be adjusted.
VMF [6:0]: Set the VCOM offset voltage.
VMF[6:0] VCOMH VCOML VMF[6:0] VCOMH VCOML
0000000 VMH VML 1000000 VMH VML
0000001 VMH – 63 VML – 63 1000001 VMH + 1 VML + 1
0000010 VMH – 62 VML – 62 1000010 VMH + 2 VML + 2
0000011 VMH – 61 VML – 61 1000011 VMH + 3 VML + 3
0000100 VMH – 60 VML – 60 1000100 VMH + 4 VML + 4
0000101 VMH – 58 VML – 58 1000101 VMH + 5 VML + 5
0000110 VMH – 58 VML – 58 1000110 VMH + 6 VML + 6
0000111 VMH – 57 VML – 57 1000111 VMH + 7 VML + 7
0001000 VMH – 56 VML – 56 1001000 VMH + 8 VML + 8
0001001 VMH – 55 VML – 55 1001001 VMH + 9 VML + 9
0001010 VMH – 54 VML – 54 1001010 VMH + 10 VML + 10
0001011 VMH – 53 VML – 53 1001011 VMH + 11 VML + 11
0001100 VMH – 52 VML – 52 1001100 VMH + 12 VML + 12
0001101 VMH – 51 VML -51 1001101 VMH + 13 VML + 13
0001110 VMH – 50 VML – 50 1001110 VMH + 14 VML + 14
0001111 VMH – 49 VML – 49 1001111 VMH + 15 VML + 15
0010000 VMH – 48 VML – 48 1010000 VMH + 16 VML + 16
0010001 VMH – 47 VML – 47 1010001 VMH + 17 VML + 17
0010010 VMH – 46 VML – 46 1010010 VMH + 18 VML + 18
0010011 VMH – 45 VML – 45 1010011 VMH + 19 VML + 19
0010100 VMH – 44 VML – 44 1010100 VMH + 20 VML + 20
0010101 VMH – 43 VML – 43 1010101 VMH + 21 VML + 21
0010110 VMH – 42 VML – 42 1010110 VMH + 22 VML + 22
0010111 VMH – 41 VML – 41 1010111 VMH + 23 VML + 23
0011000 VMH – 40 VML – 40 1011000 VMH + 24 VML + 24
0011001 VMH – 39 VML – 39 1011001 VMH + 25 VML + 25
0011010 VMH – 38 VML – 38 1011010 VMH + 26 VML + 26
0011011 VMH – 37 VML – 37 1011011 VMH + 27 VML + 27
0011100 VMH – 36 VML – 36 1011100 VMH + 28 VML + 28
0011101 VMH – 35 VML – 35 1011101 VMH + 29 VML + 29
0011110 VMH – 34 VML – 34 1011110 VMH + 30 VML + 30
0011111 VMH – 33 VML – 33 1011111 VMH + 31 VML + 31
0100000 VMH – 32 VML – 32 1100000 VMH + 32 VML + 32
0100001 VMH – 31 VML – 31 1100001 VMH + 33 VML + 33
0100010 VMH – 30 VML – 30 1100010 VMH + 34 VML + 34
0100011 VMH – 29 VML – 29 1100011 VMH + 35 VML + 35
0100100 VMH – 28 VML – 28 1100100 VMH + 36 VML + 36
0100101 VMH – 27 VML – 27 1100101 VMH + 37 VML + 37
0100110 VMH – 26 VML – 26 1100110 VMH + 38 VML + 38
0100111 VMH – 25 VML – 25 1100111 VMH + 39 VML + 39
0101000 VMH – 24 VML – 24 1101000 VMH + 40 VML + 40
0101001 VMH – 23 VML – 23 1101001 VMH + 41 VML + 41
0101010 VMH – 22 VML – 22 1101010 VMH + 42 VML + 42
0101011 VMH – 21 VML – 21 1101011 VMH + 43 VML + 43
0101100 VMH – 20 VML – 20 1101100 VMH + 44 VML + 44
0101101 VMH – 19 VML – 19 1101101 VMH + 45 VML + 45
0101110 VMH – 18 VML – 18 1101110 VMH + 46 VML + 46
0101111 VMH – 17 VML – 17 1101111 VMH + 47 VML + 47
0110000 VMH – 16 VML – 16 1110000 VMH + 48 VML + 48
0110001 VMH – 15 VML – 15 1110001 VMH + 49 VML + 49
0110010 VMH – 14 VML – 14 1110010 VMH + 50 VML + 50
0110011 VMH – 13 VML – 13 1110011 VMH + 51 VML + 51
0110100 VMH – 12 VML – 12 1110100 VMH + 52 VML + 52
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 183 of 239
0110101 VMH – 11 VML – 11 1110101 VMH + 53 VML + 53
0110110 VMH – 10 VML – 10 1110110 VMH + 54 VML + 54
0110111 VMH – 9 VML – 9 1110111 VMH + 55 VML + 55
0111000 VMH – 8 VML – 8 1111000 VMH + 56 VML + 56
0111001 VMH – 7 VML – 7 1111001 VMH + 57 VML + 57
0111010 VMH – 6 VML – 6 1111010 VMH + 58 VML + 58
0111011 VMH – 5 VML – 5 1111011 VMH + 59 VML + 59
0111100 VMH – 4 VML – 4 1111100 VMH + 60 VML + 60
0111101 VMH – 3 VML – 3 1111101 VMH + 61 VML + 61
0111110 VMH – 2 VML – 2 1111110 VMH + 62 VML + 62
0111111 VMH – 1 VML – 1 1111111 VMH + 63 VML + 63
Restriction EXTC should be high to enable this command
Register
Availability
Status Availability
Normal Mode ON, Idle Mode OFF, Sleep OUT Yes
Normal Mode ON, Idle Mode ON, Sleep OUT Yes
Partial Mode ON, Idle Mode OFF, Sleep OUT Yes
Partial Mode ON, Idle Mode ON, Sleep OUT Yes
Sleep IN Yes
Default
Default Value
Status
nVM VMF [6:0]
Power ON Sequence 1’b1 7’h40h
SW Reset 1’b1 7’h40h
HW Reset 1’b1 7’h40h

a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 184 of 239
8.3.20. NV Memory Write (D0h)
D0h NVMWR (NV Memory Write)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 1 1 0 1 0 0 0 0 D0h
1
st Parameter 1 1 ↑ XX 0 0 0 0 0 PGM_ADR [2:0] 00
2
ndParameter 1 1 ↑ XX PGM_DATA [7:0] XX
Description
This command is used to program the NV memory data. After a successful MTP operation, the information of PGM_DATA
[7:0] will programmed to NV memory.
PGM_ADR [2:0]: The select bits of ID1, ID2, ID3 and VMF [6:0] programming.
PGM_ADR [2:0] Programmed NV Memory Selection
0 0 0 ID1 programming
0 0 1 ID2 programming
0 1 0 ID3 programming
1 0 0 VMF [6:0] programming
Others Reserved
PGM_DATA [7:0]: The programmed data.
Restriction EXTC should be high to enable this command
Register
Availability
Status Availability
Normal Mode ON, Idle Mode OFF, Sleep OUT Yes
Normal Mode ON, Idle Mode ON, Sleep OUT Yes
Partial Mode ON, Idle Mode OFF, Sleep OUT Yes
Partial Mode ON, Idle Mode ON, Sleep OUT Yes
Sleep IN Yes
Default
Default Value
Status
PGM_ADR [2:0] PGM_DATA [7:0]
Power ON Sequence 3’b000 MTP value
SW Reset 3’b000 MTP value
HW Reset 3’b000 MTP value
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 185 of 239
8.3.21. NV Memory Protection Key (D1h)
D1h NVMPKEY (NV Memory Protection Key)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 1 1 0 1 0 0 0 1 D1h
1
stParameter 1 1 ↑ XX KEY [23:16] 55h
2
ndParameter 1 1 ↑ XX KEY [15:8] AAh
3
rdParameter 1 1 ↑ XX KEY [7:0] 66h
Description
KEY [23:0]: NV memory programming protection key. When writing MTP data to D1h, this register must be set to
0x55AA66h to enable MTP programming. If D1h register is not written with 0x55AA66h, then NV memory programming will
be aborted.
Restriction EXTC should be high to enable this command
Register
Availability
Status Availability
Normal Mode ON, Idle Mode OFF, Sleep OUT Yes
Normal Mode ON, Idle Mode ON, Sleep OUT Yes
Partial Mode ON, Idle Mode OFF, Sleep OUT Yes
Partial Mode ON, Idle Mode ON, Sleep OUT Yes
Sleep IN Yes
Default
Status Default Value
Power ON Sequence KEY [23:0]=55AA66h
SW Reset KEY [23:0]=55AA66h
HW Reset KEY [23:0]=55AA66h
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 186 of 239
8.3.22. NV Memory Status Read (D2h)
D2h RDNVM (NV Memory Status Read)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 1 1 0 1 0 0 1 0 D2h
1
st Parameter 1 ↑ 1 XX X X X X X X X X X
2
ndParameter 1 ↑ 1 XX 0 ID2_CNT [2:0] 0 ID1_CNT [2:0] XX
3
rdParameter 1 ↑ 1 XX BUSY VMF_CNT [2:0] 0 ID3_CNT [2:0] XX
Description
ID1_CNT [2:0] / ID2_CNT [2:0] / ID3_CNT [2:0] / VMF_CNT [2:0]: NV memory program record. The bits will increase “+1”
automatically after writing the PGM_DATA [7:0] to NV memory.
ID1_CNT [2:0] / ID2_CNT [2:0]
ID3_CNT [2:0] / VMF_CNT [2:0]
Description
Status Availability
0 0 0 No Programmed
0 0 1 Programmed 1 time
0 1 1 Programmed 2 times
1 1 1 Programmed 3 times
BUSY: The status bit of NV memory programming.
BUSY The Status of NV Memory
0 Idle
1 Busy
Restriction EXTC should be high to enable this command
Register
Availability
Status Availability
Normal Mode ON, Idle Mode OFF, Sleep OUT Yes
Normal Mode ON, Idle Mode ON, Sleep OUT Yes
Partial Mode ON, Idle Mode OFF, Sleep OUT Yes
Partial Mode ON, Idle Mode ON, Sleep OUT Yes
Sleep IN Yes
Default
Default Value
Status
ID3_CNT ID2_CNT ID1_CNT VMF_CNT BUSY
Power ON Sequence X X X X X
SW Reset X X X X X
HW Reset X X X X X

a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 187 of 239
8.3.23. Read ID4 (D3h)
D3h RDID4 (Read ID4)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 1 1 0 1 0 0 1 1 D3h
1
st Parameter 1 ↑ 1 XX X X X X X X X X X
2
ndParameter 1 ↑ 1 XX 0 0 0 0 0 0 0 0 00h
3
rdParameter 1 ↑ 1 XX 1 0 0 1 0 0 1 1 93h
4
th Parameter 1 ↑ 1 XX 0 1 0 0 0 0 0 1 41h
Description
Read IC device code.
The 1st parameter is dummy read period.
The 2nd parameter means the IC version.
The 3rd and 4th parameter mean the IC model name.
Restriction EXTC should be high to enable this command
Register
Availability
Status Availability
Normal Mode ON, Idle Mode OFF, Sleep OUT Yes
Normal Mode ON, Idle Mode ON, Sleep OUT Yes
Partial Mode ON, Idle Mode OFF, Sleep OUT Yes
Partial Mode ON, Idle Mode ON, Sleep OUT Yes
Sleep IN Yes
Default
Status Default Value
Power ON Sequence 24’h009341h
SW Reset 24’h009341h
HW Reset 24’h009341h
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 188 of 239
8.3.24. Positive Gamma Correction (E0h)
E0h PGAMCTRL (Positive Gamma Control)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 1 1 1 0 0 0 0 0 E0h
1
st Parameter 1 1 ↑ XX 0 0 0 0 VP63 [3:0] 08
2
ndParameter 1 1 ↑ XX 0 0 VP62 [5:0]
3
rdParameter 1 1 ↑ XX 0 0 VP61 [5:0]
4
th Parameter 1 1 ↑ X 0 0 0 0 VP59 [3:0] 05
5
th Parameter 1 1 ↑ XX 0 0 0 VP57 [4:0]
6
th Parameter 1 1 ↑ XX 0 0 0 0 VP50 [3:0] 09
7
th Parameter 1 1 ↑ XX 0 VP43 [6:0]
8
th Parameter 1 1 ↑ XX VP27 [3:0] VP36 [3:0]
9
th Parameter 1 1 ↑ XX 0 VP20 [6:0]
10thParameter 1 1 ↑ XX 0 0 0 0 VP13 [3:0] 0B
11thParameter 1 1 ↑ XX 0 0 0 VP6 [4:0]
12thParameter 1 1 ↑ XX 0 0 0 0 VP4 [3:0] 00
13thParameter 1 1 ↑ XX 0 0 VP2 [5:0]
14thParameter 1 1 ↑ XX 0 0 VP1 [5:0]
15thParameter 1 1 ↑ XX 0 0 0 0 VP0 [3:0] 00
Description Set the gray scale voltage to adjust the gamma characteristics of the TFT panel.
Restriction EXTC should be high to enable this command
Register
Availability
Status Availability
Normal Mode ON, Idle Mode OFF, Sleep OUT Yes
Normal Mode ON, Idle Mode ON, Sleep OUT Yes
Partial Mode ON, Idle Mode OFF, Sleep OUT Yes
Partial Mode ON, Idle Mode ON, Sleep OUT Yes
Sleep IN Yes
Default
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 189 of 239
8.3.25. Negative Gamma Correction (E1h)
E1h NGAMCTRL (Negative Gamma Correction)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 1 1 1 0 0 0 0 1 E1h
1
st Parameter 1 1 ↑ XX 0 0 0 0 VN63 [3:0] 08
2
ndParameter 1 1 ↑ XX 0 0 VN62 [5:0]
3
rdParameter 1 1 ↑ XX 0 0 VN61 [5:0]
4
th Parameter 1 1 ↑ XX 0 0 0 0 VN59 [3:0] 07
5
th Parameter 1 1 ↑ XX 0 0 0 VN57 [4:0]
6
th Parameter 1 1 ↑ XX 0 0 0 0 VN50 [3:0] 05
7
th Parameter 1 1 ↑ XX 0 VN43 [6:0]
8
th Parameter 1 1 ↑ XX VN36 [3:0] VN27 [3:0]
9
th Parameter 1 1 ↑ XX 0 VN20 [6:0]
10thParameter 1 1 ↑ XX 0 0 0 0 VN13 [3:0] 04
11thParameter 1 1 ↑ XX 0 0 0 VN6 [4:0]
12thParameter 1 1 ↑ XX 0 0 0 0 VN4 [3:0] 0F
13thParameter 1 1 ↑ XX 0 0 VN2 [5:0]
14thParameter 1 1 ↑ XX 0 0 VN1 [5:0]
15thParameter 1 1 ↑ XX 0 0 0 0 VN0 [3:0] 0F
Description Set the gray scale voltage to adjust the gamma characteristics of the TFT panel.
Restriction EXTC should be high to enable this command
Register
Availability
Status Availability
Normal Mode ON, Idle Mode OFF, Sleep OUT Yes
Normal Mode ON, Idle Mode ON, Sleep OUT Yes
Partial Mode ON, Idle Mode OFF, Sleep OUT Yes
Partial Mode ON, Idle Mode ON, Sleep OUT Yes
Sleep IN Yes
Default
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 190 of 239
8.3.26. Digital Gamma Control 1 (E2h)
E2h DGAMCTRL (Digital Gamma Control 1)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 1 1 1 0 0 0 1 0 E2h
1
st Parameter 1 1 ↑ XX RCA0 [3:0] BCA0 [3:0] XX
: 1 1 ↑ XX RCAx [3:0] BCAx [3:0] XX
16th Parameter 1 1 ↑ XX RCA15 [3:0] BCA15 [3:0] XX
Description
RCAx [3:0]: Gamma Macro-adjustment registers for red gamma curve.
BCAx [3:0]: Gamma Macro-adjustment registers for blue gamma curve.
Restriction EXTC should be high to enable this command
Register
Availability
Status Availability
Normal Mode ON, Idle Mode OFF, Sleep OUT Yes
Normal Mode ON, Idle Mode ON, Sleep OUT Yes
Partial Mode ON, Idle Mode OFF, Sleep OUT Yes
Partial Mode ON, Idle Mode ON, Sleep OUT Yes
Sleep IN Yes
Default
Default Value
Status
RCAx [3:0] BCAx [3:0]
Power ON Sequence TBD TBD
SW Reset TBD TBD
HW Reset TBD TBD
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 191 of 239
8.3.27. Digital Gamma Control 2(E3h)
E3h DGAMCTRL (Digital Gamma Control 2)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 1 1 1 0 0 0 1 1 E3h
1
st Parameter 1 1 ↑ XX RFA0 [3:0] BFA0 [3:0] XX
: 1 1 ↑ XX RFAx [3:0] BFAx [3:0] XX
64rdParameter 1 1 ↑ XX RFA63 [3:0] BFA63 [3:0] XX
Description
RFAx [3:0]: Gamma Micro-adjustment register for red gamma curve.
BFAx [3:0]: Gamma Micro-adjustment register for blue gamma curve.
Restriction EXTC should be high to enable this command
Register
Availability
Status Availability
Normal Mode ON, Idle Mode OFF, Sleep OUT Yes
Normal Mode ON, Idle Mode ON, Sleep OUT Yes
Partial Mode ON, Idle Mode OFF, Sleep OUT Yes
Partial Mode ON, Idle Mode ON, Sleep OUT Yes
Sleep IN Yes
Default
Default Value
Status
RFAx [3:0] BFAx [3:0]
Power ON Sequence TBD TBD
SW Reset TBD TBD
HW Reset TBD TBD
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 192 of 239
8.3.28. Interface Control (F6h)
F6h IFCTL (16bits Data Format Selection)
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 1 1 1 1 0 1 1 0 F6h
1
stParameter 1 1 ↑ XX
MY*
EOR
MX*
EOR
MV*
EOR
0
BGR*
EOR
0 0
WE
MODE
01
2
ndParameter 1 1 ↑ XX 0 0 EPF [1] EPF [0] 0 0
MDT
[1]
MDT
[0]
00
3
rdParameter 1 1 ↑ XX 0 0 ENDIAN 0 DM [1] DM [0] RM RIM 00
Description
MY_EOR / MX_EOR / MV_EOR / BGR_EOR:
The set value of MADCTL is used in the IC is derived as exclusive OR between 1st Parameter of IFCTL and MADCTL
Parameter.
MDT [1:0]: Select the method of display data transferring.
WEMODE: Memory write control
WEMODE=0: When the transfer number of data exceeds (EC-SC+1)_(EP-SP+1), the exceeding data will be ignored.
WEMODE=1: When the transfer number of data exceeds (EC-SC+1)_(EP-SP+1), the column and page number will be
reset, and the exceeding data will be written into the following column and page.
ENDIAN: Select Little Endian Interface bit. At Little Endian mode, the host sends LSB data first.
ENDIAN Data transfer Mode
0 Normal (MSB first, default)
1 Little Endian (LSB first)
Note: Little Endian is valid on only 65K 8-bit and 9-bit MCU interface mode.
DB[7] DB[6] DB[5] DB[4] DB[3] DB[2] DB[1] DB[0] DB[7] DB[6] DB[5] DB[4] DB[3] DB[2] DB[1] DB[0]
R4 R3 R2 R1 R0 G5 G4 G3 G2 G1 G0 B4 B3 B2 B1 B0
1st transfer (Lower byte) 2nd transfer (Upper byte)
DB[7] DB[6] DB[5] DB[4] DB[3] DB[2] DB[1] DB[0] DB[7] DB[6] DB[5] DB[4] DB[3] DB[2] DB[1] DB[0]
Input Data
16-bit display Data
(Before expanding to
18 bits data)
DM [1:0]: Select the display operation mode.
DM [1] DM [0] Display Operation Mode
0 0 Internal clock operation
0 1 RGB Interface Mode
1 0 VSYNC interface mode
1 1 Setting disabled
The DM [1:0] setting allows switching between internal clock operation mode and external display interface operation mode.
However, switching between the RGB interface operation mode and the VSYNC interface operation mode is prohibited.
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 193 of 239
RM: Select the interface to access the GRAM.
Set RM to “1” when writing display data by the RGB interface.
RM Interface for RAM Access
0 System interface/VSYNC interface
1 RGB interface
RIM: Specify the RGB interface mode when the RGB interface is used. These bits should be set before display operation
through the RGB interface and should not be set during operation.
RIM COLMOD [6:4] RGB Interface Mode
110 (262K color) 18- bit RGB interface (1 transfer/pixel)
0
101 (65K color) 16- bit RGB interface (1 transfer/pixel)
110 (262K color) 6- bit RGB interface (3 transfer/pixel)
1
101 (65K color) 6- bit RGB interface (3 transfer/pixel)
EPF [1:0]: 65K color mode data format.
DB15 DB14 DB13 DB12 DB11 DB10 DB9 DB8 DB7 DB6 DB5 DB4 DB3 DB2 DB1 DB0
R5 R4 R3 R2 R1 0 G5 G4 G3 G2 G1 G0 B5 B4 B3 B2 B1 0
Data
Bus
Frame
Data
DB15 DB14 DB13 DB12 DB11 DB10 DB9 DB8 DB7 DB6 DB5 DB4 DB3 DB2 DB1 DB0 Read
Data
EPF=01
DB15 DB14 DB13 DB12 DB11 DB10 DB9 DB8 DB7 DB6 DB5 DB4 DB3 DB2 DB1 DB0
R5 R4 R3 R2 R1 1 G5 G4 G3 G2 G1 G0 B5 B4 B3 B2 B1 1
Data
Bus
Frame
Data
DB15 DB14 DB13 DB12 DB11 DB10 DB9 DB8 DB7 DB6 DB5 DB4 DB3 DB2 DB1 DB0 Read
Data
EPF=10
DB15 DB14 DB13 DB12 DB11 DB10 DB9 DB8 DB7 DB6 DB5 DB4 DB3 DB2 DB1 DB0
R5 R4 R3 R2 R1 R0 G5 G4 G3 G2 G1 G0 B5 B4 B3 B2 B1 B0
Data
Bus
Frame
Data
DB15 DB14 DB13 DB12 DB11 DB10 DB9 DB8 DB7 DB6 DB5 DB4 DB3 DB2 DB1 DB0 Read
Data
EPF=00
DB15 DB14 DB13 DB12 DB11 DB10 DB9 DB8 DB7 DB6 DB5 DB4 DB3 DB2 DB1 DB0
R5 R4 R3 R2 R1 R0 G5 G4 G3 G2 G1 G0 B5 B4 B3 B2 B1 B0
Data
Bus
Frame
Data
DB15 DB14 DB13 DB12 DB11 DB10 DB9 DB8 DB7 DB6 DB5 DB4 DB3 DB2 DB1 DB0 Read
Data
EPF=11 Condition Copy Condition Copy
Green Data
Input data
R/B Data
Green data =
odd
Green data =
even
By-pass G0 is copied to
R0/B0
R=B
R != B
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 194 of 239
EPF [1:0] Expand 16 bbp (R,G,B) to 18bbp (R,G,B)
00
MSB is inputted to LSB
r [5:0] = {R [4:0], R [4]}
g [5:0] = {G [5:0]}
b [5:0] = {B [4:0], B [4]}
01
“0” is inputted to LSB
r [5:0] = {R [4:0], 0}
g [5:0] = {G [5:0]}
b [5:0] = {B [4:0], 0}
Exception:
R [4:0], B[4:0] = 5’h1F → r [5:0], b[5:0] = 6’h3F
10
“1” is inputted to LSB
r [5:0] = {R [4:0], 1}
g [5:0] = {G [5:0]}
b [5:0] = {B [4:0], 1}
Exception:
R [4:0], B[4:0] = 5’h00 → r [5:0], b[5:0] = 6’h00
11
Compare R [4:0], G [5:1], B [4:0] case:
Case 1: R=G=B → r [5:0] = {R [4:0], G [0]}, g [5:0] = {G [5:0]}, b [5:0] = {B [4:0], G [0]}
Case 2: R=B≠G → r [5:0] = {R [4:0], R [4]}, g [5:0] = {G [5:0]}, b [5:0] = {B [4:0], B [0]}
Case 3: R=G≠B → r [5:0] = {R [4:0], G [0]}, g [5:0] = {G [5:0]}, b [5:0] = {B [4:0], B [0]}
Case 4: B=G≠R → r [5:0] = {R [4:0], R [4]}, g [5:0] = {G [5:0]}, b [5:0] = {B [4:0], G [0]}
Restriction EXTC should be high to enable this command
Register
Availability
Status Availability
Normal Mode ON, Idle Mode OFF, Sleep OUT Yes
Normal Mode ON, Idle Mode ON, Sleep OUT Yes
Partial Mode ON, Idle Mode OFF, Sleep OUT Yes
Partial Mode ON, Idle Mode ON, Sleep OUT Yes
Sleep IN Yes
Default
Default Value
Status
EPF [1:0] MDT [1:0] ENDIAN WEMODE DM [1:0] RM RIM
Power ON Sequence 2’b00 2’b00 1’b0 1’b1 2’b00 1’b0 1’b0
SW Reset 2’b00 2’b00 1’b0 1’b1 2’b00 1’b0 1’b0
HW Reset 2’b00 2’b00 1’b0 1’b1 2’b00 1’b0 1’b0
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 195 of 239
8.4 Description of Extend register command
8.4.1 Power control A (CBh)
CBh Power control A
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 1 1 1 1 0 1 1 0 CBh
1
stParameter 1 1 ↑ XX 0 0 1 1 1 0 0 1 39
2
ndParameter 1 1 ↑ XX 0 0 1 0 1 1 0 0 2C
3
rdParameter 1 1 ↑ XX 0 0 0 0 0 0 0 0 00
4
rdParameter 1 1 ↑ XX 0 0 1 1 0 REG_VD[2:0] 34
5rdParameter 1 1 ↑ XX 0 0 0 0 0 VBC[2:0] 02
Description
REG_VD[2:0]: vcore control
REG_VD[2:0] Vcore(V)
000 1.55
001 1.4
010 1.5
011 1.2
100 1.6
101 1.7
110 reserved
111 reserved
VBC[2:0]: ddvdh control
VBC[2:0] DDVDH(V)
000 6
001 5.9
010 5.8
011 5.7
100 5.6
101 5.5
110 5.4
111 Reserved
Restriction EXTC should be high to enable this command
Register
Availability
Status Availability
Normal Mode ON, Idle Mode OFF, Sleep OUT Yes
Normal Mode ON, Idle Mode ON, Sleep OUT Yes
Partial Mode ON, Idle Mode OFF, Sleep OUT Yes
Partial Mode ON, Idle Mode ON, Sleep OUT Yes
Sleep IN Yes
Default
Default Value
Status
Parameter1 Parameter2 Parameter3 Parameter4 Parameter5
Power ON Sequence 39 2C 00 34 02
SW Reset 39 2C 00 34 02
HW Reset 39 2C 00 34 02
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 196 of 239
8.4.2 Power control B (CFh)
CFh Power control B
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 1 1 0 0 1 1 1 1 CFh
1
stParameter 1 1 ↑ XX 0 0 0 0 0 0 0 0 00
2
ndParameter 1 1 ↑ XX 1 0 1 Power control[1:0] 0 1 0 A2
3
rdParameter 1 1 ↑ XX 1 1 1 DC_ena 0 0 0 0 F0
Description
2
nd parameter: power control[1:0]
Only setting power control [1:0]=11, the VGH and VGL voltage level follow the table below.
BT [2:0] AVDD VGH VGL
0 0 0 -VCI x 4
0 0 1
VCI x 7
-VCI x 3
0 1 0 -VCI x 4
0 1 1
VCI x 2
VCI x 6
-VCI x 3
3
rd parameter: Discharge path enable. Enable high for ESD protection
Restriction EXTC should be high to enable this command
Register
Availability
Status Availability
Normal Mode ON, Idle Mode OFF, Sleep OUT Yes
Normal Mode ON, Idle Mode ON, Sleep OUT Yes
Partial Mode ON, Idle Mode OFF, Sleep OUT Yes
Partial Mode ON, Idle Mode ON, Sleep OUT Yes
Sleep IN Yes
Default
Default Value
Status
Parameter1 Parameter2 Parameter3
Power ON Sequence 00 A2 F0
SW Reset 00 A2 F0
HW Reset 00 A2 F0
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 197 of 239
8.4.3 Driver timing control A (E8h)
F6h Driver timing control A
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 1 1 1 0 1 0 0 0 E8h
1
stParameter 1 1 ↑ XX 1 0 0 0 0 1 0 NOW 84
2
ndParameter 1 1 ↑ XX 0 0 0 EQ 0 0 0 1 11
3
rdParameter 1 1 ↑ XX 0 1 1 1 1 0 PC[1:0] 7A
Description
1
st parameter:gate driver non-overlap timing control
0:default non-overlap time
1:default + 1unit
2
nd parameter:EQ timing control
0: default – 1unit
1:default EQ timing
3
rd parameter:pre-charge timing control
11: reserved
10: default pre-charge timing
01:default – 1unit
00:default – 2unit
Restriction EXTC should be high to enable this command
Register
Availability
Status Availability
Normal Mode ON, Idle Mode OFF, Sleep OUT Yes
Normal Mode ON, Idle Mode ON, Sleep OUT Yes
Partial Mode ON, Idle Mode OFF, Sleep OUT Yes
Partial Mode ON, Idle Mode ON, Sleep OUT Yes
Sleep IN Yes
Default
Default Value
Status
Parameter1 Parameter2 Parameter3
Power ON
Sequence
84 11 7A
SW Reset 84 11 7A
HW Reset 84 11 7A
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 198 of 239
8.4.4 Driver timing control B (EAh)
F6h Driver timing control B
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 1 1 1 0 1 0 1 0 EAh
1
stParameter 1 1 ↑ XX VG_SW_T4 VG_SW_T3 VG_SW_T2 VG_SW_T1 66
2
ndParameter 1 1 ↑ XX X X X X X X 0 0 00
Description
1
st parameter:gate driver timing control
VG_SW_T1[1:0]:EQ to GND
VG_SW_T2[1:0]:EQ to DDVDH
VG_SW_T3[1:0]:EQ to DDVDH
VG_SW_T4[1:0]:EQ to GND
00: 0 unit
01: 1 unit
10: 2 unit
11: 3 unit
Restriction EXTC should be high to enable this command
Register
Availability
Status Availability
Normal Mode ON, Idle Mode OFF, Sleep OUT Yes
Normal Mode ON, Idle Mode ON, Sleep OUT Yes
Partial Mode ON, Idle Mode OFF, Sleep OUT Yes
Partial Mode ON, Idle Mode ON, Sleep OUT Yes
Sleep IN Yes
Default
Default Value
Status
Parameter1 Parameter2
Power ON Sequence 66 00
SW Reset 66 00
HW Reset 66 00
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 199 of 239
8.4.5 Power on sequence control (EDh)
F6h Power on sequence control
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 1 1 1 0 1 1 0 1 EDh
1
stParameter 1 1 ↑ XX X 1 CP1 soft start X 1 CP23 soft start 55
2
ndParameter 1 1 ↑ XX X 1 En_vcl X 1 En_ddvdh 01
3
rdParameter 1 1 ↑ XX X 1 En_vgh X 1 En_vgl 23
4
thParameter 1 1 ↑ XX DDVDH_ENH 0 0 0 0 0 0 1
Description
1
st parameter:soft start control
00:soft start keep 3 frame
01:soft start keep 2 frame
01:soft start keep 1 frame
11:disable

2
nd parameter:power on sequence control
00:1st frame enable
01:2nd frame enable
10:3rd frame enable
11:4th frame enable
3
rd parameter:DDVDH enhance mode(only for 8 external capacitors)
0: disable
1: enable
Restriction EXTC should be high to enable this command
Register
Availability
Status Availability
Normal Mode ON, Idle Mode OFF, Sleep OUT Yes
Normal Mode ON, Idle Mode ON, Sleep OUT Yes
Partial Mode ON, Idle Mode OFF, Sleep OUT Yes
Partial Mode ON, Idle Mode ON, Sleep OUT Yes
Sleep IN Yes
Default
Default Value
Status
Parameter1 Parameter2 Parameter3 Parameter4
Power ON Sequence 55 01 23 01
SW Reset 55 01 23 01
HW Reset 55 01 23 01
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 200 of 239
8.4.6 Enable 3G (F2h)
F6h Enable_3G
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 1 1 1 1 0 0 1 0 F2h
1
stParameter 1 1 ↑ XX 0 0 0 0 0 0 1 3G_enb 02
Description
1
st Parameter: Enable 3 gamma control
3G_enb high for 3 gamma control enable
Restriction EXTC should be high to enable this command
Register
Availability
Status Availability
Normal Mode ON, Idle Mode OFF, Sleep OUT Yes
Normal Mode ON, Idle Mode ON, Sleep OUT Yes
Partial Mode ON, Idle Mode OFF, Sleep OUT Yes
Partial Mode ON, Idle Mode ON, Sleep OUT Yes
Sleep IN Yes
Default
Default Value
Status
Parameter1
Power ON Sequence 02
SW Reset 02
HW Reset 02
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 201 of 239
8.4.7 Pump ratio control (F7h)
F6h Pump ratio control
D/CX RDX WRX D17-8 D7 D6 D5 D4 D3 D2 D1 D0 HEX
Command 0 1 ↑ XX 1 1 1 1 0 1 1 0 F7h
1
stParameter 1 1 ↑ XX X X Ratio[1:0] 0 0 0 0 10
Description
1
st parameter:ratio control
00:reserved
01:reserved
10:DDVDH=2xVCI
11:DDVDH=3xVCI
Restriction EXTC should be high to enable this command
Register
Availability
Status Availability
Normal Mode ON, Idle Mode OFF, Sleep OUT Yes
Normal Mode ON, Idle Mode ON, Sleep OUT Yes
Partial Mode ON, Idle Mode OFF, Sleep OUT Yes
Partial Mode ON, Idle Mode ON, Sleep OUT Yes
Sleep IN Yes
Default
Default Value
Status
Parameter1
Power ON Sequence 10
SW Reset 10
HW Reset 10
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 202 of 239 9. Display Data RAM
9.1. Configuration
The display data RAM stores display dots and consists of 1,382,400 bits (240x18x320 bits). There is no
restriction on access to the RAM even when the display data on the same address is loaded to DAC. There will
be no abnormal visible effect on the display when there is a simultaneous panel read and interface read or write
display data to the same location of the frame memory.
240 x 320 x 18 bits
Frame Memory
Column Counter
Page Counter
MCU Interface
Line Latch (720 ch)
DAC (720ch)
Amp (720 ch) Line Pointer
Panel Side
Interface Side
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 203 of 239
9.2. Memory to Display Address Mapping
9.2.1. Normal Display ON or Partial Mode ON, Vertical Scroll Mode OFF
In this mode, the content of frame memory within an area where column pointer is 0000h to 00EFh and page
pointer is 0000h to 013Fh is displayed.
To display a dot on leftmost top corner, store the dot data at (column pointer, page pointer) = (0, 0)
0U 0V 0W 0X 0Y 0Z
1V 1W 1X 1Y 1Z
2W 2X 2Y 2Z
3X 3Y 3Z
WX WY WZ
XW XX XY XZ
YV YW YX YY
ZU ZV ZW ZX ZY ZZ
YZ
Z0 Z1 Z2 Z3 Z4
Y0 Y1 Y2 Y3
X0 X1 X2
W0 W1 W2
240 X 320 X 18 Bits
Frame Memory
00 01 02 03 04 05
10 11 12 13 14
20 21 22 23
30 31 32 000h 001h
EDh
EFh
EFh
000h
001h
13Fh
320
Lines
240 Columns
240 Columns
0U 0V 0W 0X 0Y 0Z
1V 1W 1X 1Y 1Z
2W 2X 2Y 2Z
3X 3Y 3Z
WX WY WZ
XW XX XY XZ
YV YW YX YY
ZU ZV ZW ZX ZY ZZ
YZ
Z0 Z1 Z2 Z3 Z4
Y0 Y1 Y2 Y3
X0 X1 X2
W0 W1 W2
240 X 320 X 18 Bits
LCD Panel
00 01 02 03 04 05
10 11 12 13 14
20 21 22 23
30 31 32 000h 001h
EDh
EEh
EFh
000h
001h
13Fh
240 Columns
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 204 of 239
9.2.2. Vertical Scroll Mode
There is a vertical scrolling mode, which is determined by the commands “Vertical Scrolling Definition” (33h) and
“Vertical Scrolling Start Address” (37h).
The Vertical Scroll Mode function is explained by these examples in the following.
0 U 0V 0W 0 X 0 Y 0 Z
1V 1W 1 X 1 Y 1 Z
2W 2 X 2 Y 2 Z
3 X 3 Y 3 Z
W X W Y W Z
XW XX XY XZ
YV YW YX YY
ZU ZV ZW ZX ZY ZZ
YZ
Z0 Z1 Z2 Z3 Z4
Y0 Y1 Y2 Y3
X0 X1 X2
W0 W1 W 2
24 0 X 32 0 X 18 Bits
Frame Mem ory
00 01 02 03 04 05
10 11 12 13 14
20 21 22 23
30 31 32 000 h 001 h
ED h
EFh
EFh
000 h
001 h
13Fh
0U 0 V 0W 0X 0Y 0Z
1 V 1W 1X 1Y 1Z
3W 3X 3Y 3Z
4X 4Y 4Z
XZ
XX XY
YW YX YY
ZV ZW ZX ZY ZZ
YZ
Z0 Z1 Z2 Z3
Y0 Y1 Y2
X0 X1 X2
240 X 32 0 X 18 Bits
LCD Panel
00 01 02 03 04 05
10 11 12 13 14
30 31 32 33
40 41 42 000 h 001 h
ED h
EEh
EFh
000h
001h
13 Fh
13Eh
13D h
Scroll Pointer = 03h
13 Eh
13Dh
XZ
20 21 22 23 24 2U 2 V 2W 2X 2Y 2Z
TFA=2, VSA=318, BFA=0 when MADCTL ML bit = 0
Scroll area
= 318 lines
Scroll area
Top fixed area
0U 0V 0W 0X 0Y 0Z
1V 1W 1X 1Y 1Z
2W 2X 2Y 2Z
3X 3Y 3Z
WX WY WZ
XW XX XY XZ
YV YW YX YY
ZU ZV ZW ZX ZY ZZ
YZ
Z0 Z1 Z2 Z3 Z4
Y0 Y1 Y2 Y3
X0 X1 X2
W0 W1 W2
240 X 320 X 18 Bits
Frame Memory
00 01 02 03 04 05
10 11 12 13 14
20 21 22 23
30 31 32 000h 001h
EDh
EFh
EFh
000 h
001 h
13Fh
0U 0V 0W 0X 0Y 0Z
1V 1W 1X 1Y 1Z
3W 3X 3Y 3Z
4X 4Y 4Z
X0 X1 X2 XX XY
240 X 320 X 18 Bits
LCD Panel
00 01 02 03 04 05
10 11 12 13 14
30 31 32 33
40 41 42 000h 001h
EDh
EEh
EFh
000 h
001 h
13Fh
13Eh
13Dh
Scroll Pointer = 03h
13Eh
13Dh
XZ
20 21 22 23 2W 2X 2Y 2Z
TFA=2, VSA=316, BFA=2 when MADCTL ML bit = 0
YV YW YX YY
ZU ZV ZW ZX ZY ZZ
YZ
Z0 Z1 Z2 Z3 Z4
Y0 Y1 Y2 Y3
Top fixed area
Scroll area
Bottom fixed area
Scroll area
= 316lines
0U 0V 0W 0X 0Y 0Z
1V 1W 1X 1Y 1Z
2W 2X 2Y 2Z
3X 3Y 3Z
WX WY WZ
XW XX XY XZ
YV YW YX YY
ZU ZV ZW ZX ZY ZZ
YZ
Z0 Z1 Z2 Z3 Z4
Y0 Y1 Y2 Y3
X0 X1 X2
W0 W1 W2
240 X 320 X 18 Bits
Frame Memory
00 01 02 03 04 05
10 11 12 13 14
20 21 22 23
30 31 32 000h 001h
EDh
EFh
EFh
000 h
001 h
13Fh
0U 0V 0W 0X 0Y 0Z
1V 1W 1X 1Y 1Z
3W 3X 3Y 3Z
4X 4Y 4Z
30 31 32 3X 3Y
240 X 320 X 18 Bits
LCD Panel
00 01 02 03 04 05
10 11 12 13 14
30 31 32 33
40 41 42 000h 001h
EDh
EEh
EFh
000 h
001 h
13Fh
13Eh
13Dh
Scroll Pointer = 05h
13Eh
13Dh
3Z
40 41 42 43 4W 4X 4Y 4Z
TFA=2, VSA=316, BFA=4 when MADCTL ML bit = 0
YV YW YX YY
ZU ZV ZW ZX ZY ZZ
YZ
Z0 Z1 Z2 Z3 Z4
Y0 Y1 Y2 Y3
Top fixed area
Scroll area
Bottom fixed area
Scroll area
= 316lines
Note: When Vertical Scrolling Definition Parameters (TFA+VSA+BFA) ≠ 320, Scrolling Mode is undefined.
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 205 of 239
9.2.3. Vertical Scroll Example
9.2.4. Case1: TFA+VSA+BFA < 320
This setting is prohibited, unless unexpected picture will be shown.
9.2.5. Case2: TFA+VSA+BFA = 320 (Rolling Scrolling)
The operation of Rolling Scrolling is explained by these examples in the following.
Physical Line Pointer
Memory
Physical
Axis
(0,0)
VSCRSADD
Display
Axis
(0,0)
1 2
1 2
When TFA=0, VSA=320, BFA=0, VSCRSADD=40 and MADCTL ML bit = 1
Physical Line Pointer
Memory
Physical
Axis
(0,0)
VSCRSADD
Display
Axis
(0,0)
1 2
When TFA=0, VSA=320, BFA=0, VSCRSADD=40 and MADCTL ML bit = 0
Physical Line Pointer
Memory
Physical
Axis
(0,0)
VSCRSADD
Display
Axis
(0,0)
1 2
1 2 2 1
Increment
VSCRSADD
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 206 of 239
Memory Physical Line Pointer
Physical
Axis
(0,0)
VSCRSADD
Display
Axis
(0,0)
2 3
When TFA=30, VSA=290, BFA=0, VSCRSADD=80 and MADCTL ML bit = 0
1
TFA 2 3 1
TFA
Physical Line Pointer
Memory
Physical
Axis
(0,0)
VSCRSADD
Display
Axis
(0,0)
When TFA=30, VSA=290, BFA=0, VSCRSADD=80 and MADCTL ML bit = 1
Physical Line Pointer
Memory
Physical
Axis
(0,0)
VSCRSADD
Display
Axis
(0,0)
Increment
VSCRSADD
TFA
2 3 1
2 3 1
TFA
2 3
TFA
2 3
1
1
TFA
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 207 of 239
9.3. MCU to memory write/read direction
B
E
ILITEK
Data stream from MCU is
like this figure
The data is written in the order illustrated above. The Counter which dictates where in the physical memory the
data is to be written is controlled by “Memory Data Access Control” Command, Bits B5, B6, and B7 as described
below.
Physical axes
(0,0)
(0,319) (239,319)
Physical Column
Pointer
Physical Page
Pointer
MADCTL
Virtual (0,0) when
B5=don’t care,
B6=”1", B7=”0"
Virtual (0,0) when
B5=don’t care,
B6=”1", B7=”1"
Bit B5
Bit B6
Bit B7
PASET
CASET
Virtual (0,0) when
B5=don’t care,
B6=”0", B7=”1"
Virtual (0,0) when
B5=don’t care,
B6=”0", B7=”0"
Virtual Physical Pointer
Translator
B5 B6 B7 CASET PASET
0 0 0 Direct to Physical Column Pointer Direct to Physical Page Pointer
0 0 1 Direct to Physical Column Pointer Direct to (319-Physical Page Pointer)
0 1 0 Direct to (239-Physical Column Pointer) Direct to Physical Page Pointer
0 1 1 Direct to (239-Physical Column Pointer) Direct to (319-Physical Page Pointer)
1 0 0 Direct to Physical Page Pointer Direct to Physical Column Pointer
1 0 1 Direct to (319-Physical Page Pointer) Direct to Physical Column Pointer
1 1 0 Direct to Physical Page Pointer Direct to (239-Physical Column Pointer)
1 1 1 Direct to (319-Physical Page Pointer) Direct to (239-Physical Column Pointer)
Condition Column Counter Page counter
When RAMWR/RAMRD command is accepted Return to “Start column” Return to “Start Page”
Complete Pixel Read/Write action Increment by 1 No change
The Column values is large than “End Column” Return to “Start column” Increment by 1
The Page counter is large than “End Page” Return to “Start column” Return to “Start Page”
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 208 of 239
Note:
Data is always written to the Frame Memory in the same order, regardless of the Memory Write Direction set by
MADCTL bits B7, B6 and B5. The write order for each pixel unit is
One pixel unit represents 1 column and 1 page counter value on the Frame Memory.
MV MX MY
Image in the Memory
(MPU)
B
E
0 0 0
B
E
0 0 1
0 1 0
0 1 1
Display Data
Direction
Normal
MADCTR
Parameter Image in the Driver (Frame Memory)
B
E
Memory(0,0)
Counter(0,0)
Y-Mirror
B
E
Memory(0,0)
Counter(0,0)
X-Mirror
B
E
B
E
Memory(0,0) Counter(0,0)
X-Mirror
Y-Mirror
B
E
B
Memory(0,0) E
Counter(0,0)
X-Y Exchange 1 0 0
1 0 1
1 1 0
1 1 1
B
E
B
E
Counter(0,0)
X-Y Exchange
Y-Mirror
XY Exchange
X-Mirror
XY Exchange
XY-Mirror
c
B
E
B
E
B
E
B
E
B
E
B
E
Memor(0,0)
Memory(0,0)
Memory(0,0)
Memory(0,0)
Counter(0,0)
Counter(0,0)
Counter(0,0)
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 209 of 239 10. Tearing Effect Output
The Tearing Effect output line supplies to the MCU a Panel synchronization signal. This signal can be enabled or
disabled by the Tearing Effect Line Off & On commands. The mode of the Tearing Effect Signal is defined by the
parameter of the Tearing Effect Line Off & On commands.
The signal can be used by the MCU to synchronize Frame Memory Writing when displaying video images.
10.1. Tearing Effect Line Modes
Mode 1, the Tearing Effect Output signal consists of V-Sync information only:
tvdl tvdh
Vertical Time Scale
tvdh = The LCD display is not updated from the Frame Memory.
tvdl = The LCD display is updated from the Frame Memory (except Invisible Line – see below).
Mode 2, the tearing effect output signal consists of V-Sync and H-Sync information; there is one V-sync and 320
H-sync pulses per field:
thdh
V-Sync
thdl
1st
Line 320th
Line
V-Sync
Invisible
Line
thdl
thdh = The LCD display is not updated from the Frame Memory.
thdl = The LCD display is updated from the Frame Memory (except Invisible Line – see above).
Bottom Line
2
nd Line
1
st Line
TE (mode 2)
TE (mode 1)
Note: During Sleep In Mode, the Tearing Effect Output Pin is active Low.
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 210 of 239
10.2. Tearing Effect Line Timings
The tearing effect signal is described below:
tvdh
Vertical Timing
Horizontal Timing
thdl thdh
tvd l
AC characteristics of Tearing Effect Signal (Frame Rate = 60Hz)
Symbol Parameter Min. Typ. Max. Unit Description
tvdl Vertical timing low duration -- -- -- ms
tvdh Vertical timing high duration 1000 -- -- us
thdl Horizontal timing low duration -- -- -- us
thdh Horizontal timing high duration -- -- 500 us
Note:

1. The timings in Table as above apply when MADCTL B4=0 and B4=1
2. The signal’s rise and fall times (tf, tr) are stipulated to be equal to or less than 15ns.
   tr tf
   80%
   20%
   80%
   20%
   The Tearing Effect Output Line is fed back to the MCU and should be used to avoid Tearing Effect.
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 211 of 239
3. Sleep Out – Command and Self-Diagnostic Functions of the
   Display Module
   11.1. Register loading Detection
   Sleep Out-command (Command “Sleep Out (11h)”) is a trigger for an internal function of the display module,
   which indicates, if the display module loading function of factory default values from EV Memory(or similar
   device) to registers of the display controller is working properly.
   If the register loading detection is successfully, there is inverted (= increased by 1) a bit, which is defined in
   command “Read Display Self-Diagnostic Result (0Fh)” (= RDDSDR) (The used bit of this command is D7). If it is
   failure, this bit (D7) is not inverted (= not increased by 1).
   The flow chart for this internal function is following:
   Power on sequence
   HW reset
   SW reset
   RDDSDR(0Fh)'s D7 = '0' Sleep IN
   mode
   Sleep OUT
   mode
   Sleep IN (10h)
   Sleep OUT (11h)
   Successful ?
   D7 inverted
   Register Loading Detection YES
   ON
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 212 of 239
   11.2. Functionality Detection
   Sleep Out-command (Command “Sleep Out (11h)”) is a trigger for an internal function of the display module,
   which indicates, if the display module is still running and meets functionality requirements.
   The internal function (= the display controller) is comparing, if the display module is still meeting functionality
   requirements (e.g. booster voltage levels, timings, etc.) If functionality requirement is met, there is an inverted (=
   increased by 1) bit, which defined in command “Read Display Self- Diagnostic Result (0Fh)” (= RDDSDR) (The
   used bit of this command is D6). If functionality requirement is not same, this bit (D6) is not inverted (= increased
   by 1). The flow chart for this internal function is shown as below.
   The flow chart for this internal function is following:
   Power on sequence
   HW reset
   SW reset
   RDDSDR(0Fh)'s D6 = '0' Sleep IN
   mode
   Sleep OUT
   mode
   Sleep IN (10h)
   Sleep OUT (11h)
   Check timings, valtage levels,
   and other functionalities
   Is the required
   functionality present?
   D6 inverted YES
   NO
   Note 1: There is needed 120msec after Sleep Out -command, when there is changing from Sleep In –mode to
   Sleep Out -mode, before there is possible to check if User’s functionality requirements are met and a
   value of RDDSDR’s D6 is valid. Otherwise, there is 5msec delay for D6’s value, when Sleep
   Out –command is sent in Sleep Out -mode.

a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 213 of 239 12. Power ON/OFF Sequence
VDDI and VCI can be applied in any order.
VCI and VDDI can be powered down in any order.
During power off, if LCD is in the Sleep Out mode, VCI and VDDI must be powered down minimum
120msec after RESX has been released.
During power off, if LCD is in the Sleep In mode, VDDI or VCI can be powered down minimum 0msec after
RESX has been released.
CSX can be applied at any timing or can be permanently grounded. RESX has priority over CSX.
Note 1: There will be no damage to the display module if the power sequences are not met.
Note 2: There will be no abnormal visible effects on the display panel during the Power On/Off Sequences.
Note 3: There will be no abnormal visible effects on the display between end of Power On Sequence and before
receiving Sleep Out command. Also between receiving Sleep In command and Power Off Sequence.
Note 4: If RESX line is not held stable by host during Power On Sequence as defined in Sections 12.1 and 12.2,
then it will be necessary to apply a Hardware Reset (RESX) after Host Power On Sequence is complete
to ensure correct operation. Otherwise function is not guaranteed.
12.1. Case 1 – RESX line is held High or Unstable by Host at Power ON
If RESX line is held High or unstable by the host during Power On, then a Hardware Reset must be applied after
both VCI and VDDI have been applied – otherwise correct functionality is not guaranteed. There is no timing
restriction upon this hardware reset.
Note 1: Unless otherwise specified, timings herein show cross point at 50% of signal power level.
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 214 of 239
12.2. Case 2 – RESX line is held Low by Host at Power ON
If RESX line is held Low (and stable) by the host during Power On, then the RESX must be held low for minimum
10µsec after both VCI and VDDI have been applied.
Note 1: Unless otherwise specified, timings herein show cross point at 50% of signal power level.
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 215 of 239
12.3. Uncontrolled Power Off
The uncontrolled power off means a situation when e.g. there is removed a battery without the controlled power
off sequence. There will not be any damages for the display module or the display module will not cause any
damages for the host or lines of the interface. At an uncontrolled power off event, ILI9341 will force the display to
blank and will not be any abnormal visible effects with in 1 second on the display and remains blank until “Power
On Sequence” actives.
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 216 of 239 13. Power Level Definition
13.1. Power Levels
7 level modes are defined they are in order of Maximum Power consumption to Minimum Power Consumption:

1. Normal Mode On (full display), Idle Mode Off, Sleep Out.
   In this mode, the display is able to show maximum 262,144 colors.
2. Partial Mode On, Idle Mode Off, Sleep Out.
   In this mode part of the display is used with maximum 262,144 colors.
3. Normal Mode On (full display), Idle Mode On, Sleep Out.
   In this mode, the full display area is used but with 8 colors.
4. Partial Mode On, Idle Mode On, Sleep Out.
   In this mode, part of the display is used but with 8 colors.
5. Sleep In Mode.
   In this mode, the DC : DC converter, Internal oscillator and panel driver circuit are stopped. Only the MCU
   interface and memory works with VDDI power supply. Contents of the memory are safe.
6. Power Off Mode.
   In this mode, both VCI and VDDI are removed.
   Note1: Transition between modes 1-5 is controllable by MCU commands.
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 217 of 239
   13.2. Power Flow Chart
   Power ON sequence
   HW reset
   SW reset
   Sleep IN
   Normal display mode ON
   Idle mode OFF
   Sleep IN
   Normal display mode ON
   Idle mode ON
   Sleep IN
   Partial mode ON
   Idle mode OFF
   Sleep IN
   Partial mode ON
   Idle mode ON
   Sleep OUT
   Normal display mode ON
   Idle mode OFF
   Sleep OUT
   Normal display mode ON
   Idle mode ON
   Sleep OUT
   Partial mode ON
   Idle mode OFF
   Sleep OUT
   Partial mode ON
   Idle mode ON
   SLPIN
   SLPOUT
   SLPIN
   SLPOUT
   SLPIN
   SLPOUT
   SLPIN
   SLPOUT
   NORON
   PTLON
   NORON
   PTLON
   IDMON IDMOFF
   IDMON IDMOFF
   NORON
   PTLON
   NORON
   PTLON
   IDMON IDMOFF
   IDMON IDMOFF
   Normal display mode ON = NORON
   Partial mode ON = PTLON
   Idle mode OFF = IDMOFF
   Sleep OUT = SLPOUT
   Sleep IN = SLPIN
   Note 1: There is not any abnormal visual effect when there is changing from one power mode to another power
   mode.
   Note 2: There is not any limitation, which is not specified by User, when there is changing from one power mode
   to another power mode.
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 218 of 239
7. Gamma Curves Selection
   ILI9341 provide one gamma curve Gamma2.2. The gamma curve can be selected by the GC0 settings.
   14.1. Gamma Default Values (for NW type LC)
   Output Voltage
   Data VCOM = Low VCOM = High
   Gamma 2.2 Gamma 2.2
   0 V0P 4.084 V0N 0.277
   1 V1P 4.015 V1N 0.346
   2 V2P 3.843 V2N 0.482
   3 V3P 3.681 V3N 0.629
   4 V4P 3.518 V4N 0.776
   5 V5P 3.445 V5N 0.924
   6 V6P 3.371 V6N 1.071
   7 V7P 3.285 V7N 1.157
   8 V8P 3.199 V8N 1.242
   9 V9P 3.128 V9N 1.314
   10 V10P 3.056 V10N 1.385
   11 V11P 2.985 V11N 1.456
   12 V12P 2.928 V12N 1.513
   13 V13P 2.871 V13N 1.570
   14 V14P 2.802 V14N 1.619
   15 V15P 2.733 V15N 1.668
   16 V16P 2.674 V16N 1.710
   17 V17P 2.615 V17N 1.753
   18 V18P 2.557 V18N 1.795
   19 V19P 2.508 V19N 1.830
   20 V20P 2.458 V20N 1.865
   21 V21P 2.425 V21N 1.899
   22 V22P 2.391 V22N 1.932
   23 V23P 2.357 V23N 1.966
   24 V24P 2.323 V24N 2.000
   25 V25P 2.289 V25N 2.034
   26 V26P 2.256 V26N 2.068
   27 V27P 2.222 V27N 2.102
   28 V28P 2.193 V28N 2.129
   29 V29P 2.165 V29N 2.155
   30 V30P 2.136 V30N 2.182
   31 V31P 2.108 V31N 2.208
   32 V32P 2.080 V32N 2.235
   33 V33P 2.051 V33N 2.262
   34 V34P 2.023 V34N 2.288
   35 V35P 1.994 V35N 2.315
   36 V36P 1.966 V36N 2.342
   37 V37P 1.942 V37N 2.368
   38 V38P 1.917 V38N 2.395
   39 V39P 1.893 V39N 2.421
   40 V40P 1.869 V40N 2.448
   41 V41P 1.845 V41N 2.475
   42 V42P 1.820 V42N 2.501
   43 V43P 1.796 V43N 2.528
   44 V44P 1.776 V44N 2.549
   45 V45P 1.755 V45N 2.571
   46 V46P 1.730 V46N 2.597
   47 V47P 1.706 V47N 2.623
   48 V48P 1.681 V48N 2.649
   49 V49P 1.653 V49N 2.679
   50 V50P 1.624 V50N 2.710
   51 V51P 1.598 V51N 2.735
   52 V52P 1.573 V52N 2.761
   53 V53P 1.541 V53N 2.793
   54 V54P 1.508 V54N 2.825
   55 V55P 1.476 V55N 2.857
   56 V56P 1.438 V56N 2.895
   57 V57P 1.400 V57N 2.933
   58 V58P 1.359 V58N 2.982
   59 V59P 1.319 V59N 3.031
   60 V60P 1.246 V60N 3.109
   61 V61P 1.173 V61N 3.186
   62 V62P 1.070 V62N 3.289
   63 V63P 0.279 V63N 4.083
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 219 of 239
   14.2. Gamma Curves
   14.2.1. Gamma Curve 1 (GC0), applies the function y=x2.2
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 220 of 239
   14.3. Gamma Curves
   14.3.1. Grayscale Voltage Generation
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 221 of 239
   14.3.2. Positive Gamma Correction
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 222 of 239
   14.3.3. Negative Gamma Correction
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 223 of 239
8. Reset
   15.1. Registers
   The registers that are initialized are listed as below:
   After
   Powered ON
   After
   Hardware Reset
   After
   Software Reset
   Frame Memory Random Repair data No Change
   Sleep In In In
   Display Mode Normal Normal Normal
   Display Off Off Off
   Idle Off Off Off
   Column Start Address 0000 h 0000 h 0000 h
   Column End Address 00EF h 00EF h If MADCTL’s B5=0:00EF h
   If MADCTL’s B5=1:013F h
   Page Start Address 0000 h 0000 h 0000 h
   Page End Address 013F h 013F h If MADCTL’s B5 = 0:013F h
   If MADCTL’s B5=1:00EF h
   Gamma Setting GC0 GC0 GC0
   Partial Area Start 0000 h 0000 h 0000 h
   Partial Area End 013F h 013F h 013F h
   Memory Data Access
   Control 00 h 00 h No Change
   RDDPM 08 h 08 h 08 h
   RDDMADCTL 00 h 00 h No Change
   RDDCOLMOD 06 h 06 h 06 h
   RDDIM 00 h 00 h 00 h
   RDDSM 00 h 00 h 00 h
   RDDSDR 00 h 00 h 00 h
   TE Output Line Off Off Off
   TE Line Mode Mode 1 (Note 3) Mode 1 (Note 3) Mode 1 (Note 3)
   Note 1: There will be no abnormal visible effects on the display when S/W or H/W Resets are applied.
   Note 2: After Powered-On Reset finishes within 10µs after both VCI & VDDI are applied.
   Note 3: Mode 1 means Tearing Effect Output Line consists of V-Blanking Information only.
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 224 of 239
   15.2. Output Pins, I/O Pins
   After
   Power ON
   After
   Hardware Reset
   After
   Software Reset
   TE line Low Low Low
   D[17:0] (output driver) Hi-Z (Inactive) Hi-Z (Inactive) Hi-Z (Inactive)
   Note 1: There will be no output from D [17:0] during Power ON/OFF sequence, hardware reset and software
   reset.
   15.3. Input Pins
   During
   Power ON
   Process
   After
   Power
   ON
   After
   Hardware
   Reset
   After
   Software
   Reset
   During
   Power OFF
   Process
   RESX See Chapter 12 Input valid Input valid Input valid See Chapter 12
   CSX Input invalid Input valid Input valid Input valid Input invalid
   D/CX Input invalid Input valid Input valid Input valid Input invalid
   WRX Input invalid Input valid Input valid Input valid Input invalid
   RDX Input invalid Input valid Input valid Input valid Input invalid
   D[17:0] (input driver) Input invalid Input valid Input valid Input valid Input invalid
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 225 of 239
   15.4. Reset Timing
   Shorter than 5us
   tRW
   tRT
   Normal operation Resetting Initial condition
   (Default for H/W reset)
   RESX
   Display Status
   Signal Symbol Parameter Min Max Unit
   RESX tRW Reset pulse duration 10 uS
   5
   (note 1,5) mS
   tRT Reset cancel 120
   (note 1,6,7) mS
   Note 1: The reset cancel includes also required time for loading ID bytes, VCOM setting and other settings from
   NV memory to registers. This loading is done every time when there is HW reset cancel time (tRT)
   within 5 ms after a rising edge of RESX.
   Note 2: Spike due to an electrostatic discharge on RESX line does not cause irregular system reset according to
   the table below: -
   RESX Pulse Action
   Shorter than 5us Reset Rejected
   Longer than 10us Reset
   Between 5us and 10us Reset starts
   Note 3: During the Resetting period, the display will be blanked (The display is entering blanking sequence,
   which maximum time is 120 ms, when Reset Starts in Sleep Out –mode. The display remains the blank
   state in Sleep In -mode.) And then return to Default condition for Hardware Reset.
   Note 4: Spike Rejection also applies during a valid reset pulse as shown below:
   Note 5: When Reset applied during Sleep In Mode.
   Note 6: When Reset applied during Sleep Out Mode.
   Note 7: It is necessary to wait 5msec after releasing RESX before sending commands. Also Sleep Out
   command cannot be sent for 120msec.
   a-Si TFT LCD Single Chip Driver
   240RGBx320 Resolution and 262K color ILI9341
   The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
   reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
   Page 226 of 239
9. Configuration of Power Supply Circuit
   G[16]
   G[14]
   G[12]
   G[10]
   G[8]
   G[6]
   G[4]
   G[2]
   DUMMY
   DUMMY
   DUMMY
   DUMMY
   DUMMY
   VCOM
   VCOM
   VCOM
   VCOM
   VCOM
   VCOM
   VCOM
   VCOM
   S[355]
   S[356]
   S[357]
   S[358]
   S[359]
   S[360]
   DUMMY
   DUMMY
   DUMMY
   G[1]
   G[3]
   G[5]
   G[7]
   G[9]
   G[11]
   G[13]
   G[15]
   S[1]
   S[2]
   S[3]
   S[4]
   S[5]
   S[6]
   S[7]
   S[8]
   S[9]
   S[10]
   DUMMY
   C22P
   C22P
   C22M
   C22M
   C21P
   C21P
   C21M
   C21M
   VGH
   VGH
   VGH
   VGH
   VGH
   DUMMY
   VGL
   VGL
   VGL
   VGL
   VGL
   VGL
   AVDD
   AVDD
   AVDD
   AVDD
   AVDD
   AVDD
   AVDD
   C12P
   C12P
   C12P
   C12P
   C12P
   C12P
   C12P
   C12M
   C12M
   C12M
   C12M
   C12M
   C12M
   C12M
   C11P
   C11P
   C11P
   C11P
   C11P
   C11P
   C11P
   C11M
   C11M
   C11M
   C11M
   C11M
   C11M
   C11M
   DUMMY
   DUMMY
   DUMMY
   DUMMY
   DUMMY
   DUMMY
   DUMMY
   VCI
   VCI
   VCI
   VCI
   VCI
   VCI
   VCI
   VCI
   VSS3
   VSS3
   VSS3
   VSS
   VSS
   VSS
   VSS
   VSS
   VSS
   VSSC
   VSSC
   VSSC
   VSSC
   VSSC
   VSSC
   VSSC
   VSSA
   VSSA
   VSSA
   VSSA
   VSSA
   VSSA
   VSSA
   VSSA
   DUMMY
   VGS
   VGS
   EXTC
   IM[3]
   IM[2]
   IM[1]
   IM[0]
   RESX
   CSX
   DCX
   WRX
   RDX
   DUMMY
   VSYNC
   HSYNC
   ENABL
   DOTCLK
   DUMMY
   SDA
   DB[0]
   DB[1]
   DB[2]
   DB[3]
   DUMMY
   DB[4]
   DB[5]
   DB[6]
   DB[7]
   DUMMY
   DB[8]
   DB[9]
   DB[10]
   DB[11]
   DUMMY
   DB[12]
   DB[13]
   DB[14]
   DB[15]
   DUMMY
   DB[16]
   DB[17]
   DUMMY
   TE
   SDO
   DUMMY
   VDDI
   VDDI
   VDDI
   VDDI
   VDDI
   VDDI
   VDDI
   Vcore
   Vcore
   Vcore
   Vcore
   Vcore
   Vcore
   Vcore
   Vcore
   Vcore
   Vcore
   Vcore
   Vcore
   Vcore
   Vcore
   DUMMY
   GVDD
   GVDD
   GVDD
   GVDD
   DUMMY
   DUMMY
   VCL
   VCL
   VCL
   VCL
   VCL
   VCL
   VCL
   VCL
   DUMMY
   DUMMY
   DUMMY
   DUMMY
   DUMMY
   DUMMY
   DUMMY
   DUMMY
   DUMMY
   DUMMY
   DUMMY
   DUMMY
   DUMMY
   DUMMY
   DUMMY
   DUMMY
   DUMMY
   DUMMY
   DUMMY
   DUMMY
   DUMMY
   DUMMY
   DUMMY
   DUMMY
   DUMMY
   VCOM
   VCOM
   VCOM
   VCOM
   VCOM
   VCOM
   VCOM
   VCOM
   DUMMY
   DUMMY
   G[320]
   G[318]
   G[316]
   G[314]
   G[312]
   G[310]
   G[308]
   G[306]
   G[304]
   G[302]
   S[709]
   S[710]
   S[711]
   S[712]
   S[713]
   S[714]
   S[715]
   S[716]
   S[717]
   S[718]
   S[719]
   S[720]
   S[361]
   S[362]
   S[363]
   S[364]
   S[365]
   S[366]
   G[303]
   G[305]
   G[307]
   G[309]
   G[311]
   G[313]
   G[315]
   G[317]
   G[319]
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   















 




    







































 

 
 




VCOM To Panel
VCOM To Panel
 
 
!"#$

  !" ##$%%
BC
BC_CT
VDDI_LED
VDDI_LED
DB[18]\_Dummy
DB[19]\_Dummy
DB[20]\_Dummy
DB[21]\_Dummy
DB[22]\_Dummy
DB[23]\_Dummy


%

a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 227 of 239
The Following tables shows specifications of external elements connected to the ILI9341’s power supply circuit.
Items Recommended
Specification Pin connection
6.3V AVDD ,VCL,C11P/M,C12P/M,
10V C21P/M,C22P/M Capacity
1 µF (B characteristics)
25V VGL, VGH
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 228 of 239 17. NV Memory Programming Flow
Start
Reset
Check (D2h)
ID3*CNT/ID2_CNT
ID1_CNT/VMF_CNT
=3'b111
Wait 10ms
Wait 10ms
Reset
End
Y
NV Memory Protection Key (D1h)
1
st Parameter : 55h
2
nd Parameter : AAh
3
rd Parameter : 66h
NV Memory Write (D0h)
1
st Parameter : PGM_ADR[2:0]=3'bxxx
2
nd Parameter : PGM* DATA[7:0]=8'bxx
(xx=8 bit OTP value)
N
Sleep out(11h)
Wait 100ms
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 229 of 239 18. Electrical Characteristics
18.1 Absolute Maximum Ratings
The absolute maximum rating is listed on following table. When ILI9341 is used out of the absolute maximum
ratings, ILI9341 may be permanently damaged. To use ILI9341 within the following electrical characteristics
limitation is strongly recommended for normal operation. If these electrical characteristic conditions are
exceeded during normal operation, ILI9341 will malfunction and cause poor reliability.
Item Symbol Unit Value
Supply voltage VCI V -0.3 ~ +4.6
Supply voltage (Logic) VDDI V -0.3 ~ +4.6
Supply voltage (Digital) VCORE V -0.3 ~ +2.0
Driver supply voltage VGH-VGL V -0.3 ~ +32.0
Logic input voltage range VIN V -0.3 ~ VDDI + 0.3
Logic output voltage range VO V -0.3 ~ VDDI + 0.3
Operating temperature Topr ℃ -40 ~ +85
Storage temperature Tstg ℃ -55 ~ +110
Note: If the absolute maximum rating of even is one of the above parameters is exceeded even
momentarily, the quality of the product may be degraded. Absolute maximum ratings, therefore,
specify the values exceeding which the product may be physically damaged. Be sure to use the
product within the range of the absolute maximum ratings.
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 230 of 239
18.2 DC Characteristics
18.2.1 General DC Characteristics
Item Symbol Unit Condition Min. Typ. Max. Note
Power and Operation Voltage
Analog Operating
Voltage VCI V Operating voltage 2.5 2.8 3.3 Note2
Logic Operating
Voltage VDDI V I/O supply voltage 1.65 2.8 3.3 Note2
Digital Operating
voltage VCORE V Digital supply voltage - 1.5 - Note2
Gate Driver High
Voltage VGH V - 10.0 - 16.0 Note3
Gate Driver Low
Voltage VGL V - -16.0 - -9.0 Note3
Driver Supply Voltage - V |VGH-VGL| 19 - 32 Note3
Input and Output
Logic High Level Input
Voltage VIH V - 0.7*VDDI - VDDI Note1,2,3
Logic Low Level Input
Voltage VIL V - VSS - 0.3*VDDI Note1,2,3
Logic High Level
Output Voltage VOH V IOL=-1.0mA 0.8*VDDI - VDDI Note1,2,3
Logic Low Level
Output Voltage VOL V IOL=1.0mA VSS - 0.2*VDDI Note1,2,3
Logic High Level Input
Current IIH uA - - - 1 Note1,2,3
Logic Low Level input
Current IIL uA - -1 - - Note1,2,3
Logic Input Leakage
Current ILEA uA VIN=VDDI or VSS -0.1 - +0.1 Note1,2,3
VCOM Operation
VCOM High Voltage VCOMH V Ccom=12nF 2.5 - 5.0 Note3
VCOM Low Voltage VCOML V Ccom=12nF -2.5 - 0.0 Note3
VCOM Amplitude
Voltage VCOMA V |VCOMH-VCOML| 4.0 - 5.5 Note3
Source Driver
Source Output Range Vsout V - 0.1 - AVDD-0.1 Note4
Gamma Reference
Voltage GVDD V - 3.0 - 5.0 Note3
Sout>=4.2V
Sout<=0.8V - - 20 Note4 Output Deviation
Voltage (Source
Output channel)
Vdev mV
4.2V>Sout>0.8V - - 15 -
Output Offset Voltage VOFSET mV - - - 35 Note7
Booster Operation
1
st Booster (VCIx2)
Voltage AVDD V - 4.95
(Note 5) -
5.5
(Note 6) Note3
1
st Booster (VCIx2
Drop Voltage
VCIx2
drop % loading=1mA - - 5 Note3
Liner Range Vliner V - 0.2 - AVDD-0.2
Note 1: VDDI=1.65 to 3.3V, VCI=2.5 to 3.3V, AGND=VSS=0V, Ta=-30 to 70 (to +85 no damage) ℃.
Note2: Please supply digital VDDI voltage equal or less than analog VCI voltage.
Note3: CSX, RDX, WRX, D[17:0], D/CX, RESX, TE, DOTCLK, VSYNC, HSYNC, DE, SDA, SCL, IM3, IM2, IM1,
IM0, and Test pins.
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 231 of 239
Note4: When the measurements are performed with LCD module. Measurement Points are like Note3.
Note5: VCI=2.6V
Note6: VCI=3.3V
Note7: The Max. Value is between with Note 4 measure point and Gamma setting value
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 232 of 239
18.3 AC Characteristics
18.3.1 Display Parallel 18/16/9/8-bit Interface Timing Characteristics (8080-Ⅰ system)
tast
D/CX
CSX
WRX
D[17:0]
(Write)
RDX
D[17:0]
(Read)
tcs
twrl
tcsf
twrh
twc
taht
tdst tdht
tast trcs / trcsfm
trc / trcfm
trdl / trdlfm
trdh / trdhfm
taht
trat / tratfm trodh
tchw tchw
Signal Symbol Parameter min max Unit Description
tast Address setup time 0 - ns DCX
taht Address hold time (Write/Read) 0 - ns
tchw CSX “H” pulse width 0 - ns
tcs Chip Select setup time (Write) 15 - ns
trcs Chip Select setup time (Read ID) 45 - ns
trcsfm Chip Select setup time (Read FM) 355 - ns
CSX
tcsf Chip Select Wait time (Write/Read) 10 - ns
twc Write cycle 66 - ns
WRX twrh Write Control pulse H duration 15 - ns
twrl Write Control pulse L duration 15 - ns
trcfm Read Cycle (FM) 450 - ns
RDX (FM) trdhfm Read Control H duration (FM) 90 - ns
trdlfm Read Control L duration (FM) 355 - ns
trc Read cycle (ID) 160 - ns
RDX (ID) trdh Read Control pulse H duration 90 - ns
trdl Read Control pulse L duration 45 - ns
tdst Write data setup time 10 - ns
tdht Write data hold time 10 - ns
trat Read access time - 40 ns
tratfm Read access time - 340 ns
D[17:0],
D[15:0],
D[8:0],
D[7:0]
trod Read output disable time 20 80 ns
For maximum CL=30pF
For minimum CL=8pF
Note: Ta = -30 to 70 °C, VDDI=1.65V to 3.3V, VCI=2.5V to 3.3V, VSS=0V
tr≦15ns
70%
30%
70%
30%
tf≦15ns
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 233 of 239
CSX timings :
CSX
WRX,
RDX
tcsf Min. 5ns
tchw
Note: Logic high and low levels are specified as 30% and 70% of VDDI for Input signals.
Write to read or read to write timings:
twrh
trdh
trdhfm
CSX
WRX
RDX
‘0’
Note: Logic high and low levels are specified as 30% and 70% of VDDI for Input signals.
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 234 of 239
18.3.2 Display Parallel 18/16/9/8-bit Interface Timing Characteristics(8080-Ⅱ system)
tast
D/CX
CSX
WRX
D[17:0]
(Write)
RDX
D[17:0]
(Read)
tcs
twrl
tcsf
twrh
twc
taht
tdst tdht
tast trcs / trcsfm
trc / trcfm
trdl / trdlfm
trdh / trdhfm
taht
trat / tratfm trodh
tchw tchw
Signal Symbo
l Parameter min max Unit Description
tast Address setup time 0 - ns DCX
taht Address hold time (Write/Read) 0 - ns
tchw CSX “H” pulse width 0 - ns
tcs Chip Select setup time (Write) 15 - ns
trcs Chip Select setup time (Read ID) 45 - ns
trcsfm Chip Select setup time (Read FM) 355 - ns
CSX
tcsf Chip Select Wait time (Write/Read) 10 - ns
twc Write cycle 66 - ns
WRX twrh Write Control pulse H duration 15 - ns
twrl Write Control pulse L duration 15 - ns
trcfm Read Cycle (FM) 450 - ns
RDX (FM) trdhfm Read Control H duration (FM) 90 - ns
trdlfm Read Control L duration (FM) 355 - ns
trc Read cycle (ID) 160 - ns
RDX (ID) trdh Read Control pulse H duration 90 - ns
trdl Read Control pulse L duration 45 - ns
tdst Write data setup time 10 - ns
tdht Write data hold time 10 - ns
trat Read access time - 40 ns
tratfm Read access time - 340 ns
D[17:0],
D[17:10]&D[8:1],
D[17:10],
D[17:9]
trod Read output disable time 20 80 ns
For maximum CL=30pF
For minimum CL=8pF
Note: Ta = -30 to 70 °C, VDDI=1.65V to 3.3V, VCI=2.5V to 3.3V, VSS=0V.
tr≦15ns
70%
30%
70%
30%
tf≦15ns
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 235 of 239
CSX timings :
CSX
WRX,
RDX
tcsf Min. 5ns
tchw
Note: Logic high and low levels are specified as 30% and 70% of VDDI for Input signals.
Write to read or read to write timings:
twrh
trdh
trdhfm
CSX
WRX
RDX
‘0’
Note: Logic high and low levels are specified as 30% and 70% of VDDI for Input signals.
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 236 of 239
18.3.3 Display Serial Interface Timing Characteristics (3-line SPI system)
Signal Symbol Parameter min max Unit Description
tscycw Serial Clock Cycle (Write) 100 - ns
tshw SCL “H” Pulse Width (Write) 40 - ns
tslw SCL “L” Pulse Width (Write) 40 - ns
tscycr Serial Clock Cycle (Read) 150 - ns
tshr SCL “H” Pulse Width (Read) 60 - ns
SCL
tslr SCL “L” Pulse Width (Read) 60 - ns
SDA / SDI tsds Data setup time (Write) 30 - ns
(Input) tsdh Data hold time (Write) 30 - ns
SDA / SDO tacc Access time (Read) 10 - ns
(Output) toh Output disable time (Read) 10 50 ns
tscc SCL-CSX 20 - ns
tchw CSX “H” Pulse Width 40 - ns
tcss 60 - ns
CSX
tcsh
CSX-SCL Time
65 - ns
Note: Ta = 25 °C, VDDI=1.65V to 3.3V, VCI=2.5V to 3.3V, AGND=VSS=0V
tr≦15ns
70%
30%
70%
30%
tf≦15ns
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 237 of 239
18.3.4 Display Serial Interface Timing Characteristics (4-line SPI system)
tcss
CSX
D/CX
SCL
SDA (SDI)
SDA (SDO)
tcsh
tas tah
twrl/trdl twrh/trdh
twc/trc
tacc tod
tds tdh
Signal Symbol Parameter min max Unit Description
tcss Chip select time (Write) 40 - ns CSX
tcsh Chip select hold time (Read) 40 - ns
twc Serial clock cycle (Write) 100 - ns
twrh SCL “H” pulse width (Write) 40 - ns
twrl SCL “L” pulse width (Write) 40 - ns
trc Serial clock cycle (Read) 150 - ns
trdh SCL “H” pulse width (Read) 60 - ns
SCL
trdl SCL “L” pulse width (Read) 60 - ns
tas D/CX setup time 10 - D/CX
tah D/CX hold time (Write / Read) 10 -
SDA / SDI tds Data setup time (Write) 30 - ns
(Input) tdh Data hold time (Write) 30 - ns
SDA / SDO tacc Access time (Read) 10 - ns
(Output) tod Output disable time (Read) 10 50 ns
For maximum CL=30pF
For minimum CL=8pF
Note: Ta = 25 °C, VDDI=1.65V to 3.3V, VCI=2.5V to 3.3V, AGND=VSS=0V
tr≦15ns
70%
30%
70%
30%
tf≦15ns
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 238 of 239
18.3.5 Parallel 18/16/6-bit RGB Interface Timing Characteristics
trgbf
trgbr
tSYNCS
VIH
VIL
tENS tENH
trgbf trgbr
tPDS tPDH
tCYCD
PWDL PWDH
VIH
VIH
VIH VIH
VIH VIH
VIH
VIL VIL
VIL
VIL
VIL
VIL
VSYNC
HSYNC
ENABLE
Write Data
DOTCLK
D[17:0]
Signal Symbol Parameter min max Unit Description
VSYNC / tSYNCS VSYNC/HSYNC setup time 15 - ns
HSYNC tSYNCH VSYNC/HSYNC hold time 15 - ns
tENS DE setup time 15 - ns DE
tENH DE hold time 15 - ns
tPOS Data setup time 15 - ns D[17:0]
tPDH Data hold time 15 - ns
PWDH DOTCLK high-level period 15 - ns
PWDL DOTCLK low-level period 15 - ns
tCYCD DOTCLK cycle time 100 - ns
DOTCLK
trgbr , trgbf DOTCLK,HSYNC,VSYNC rise/fall time - 15 ns
18/16-bit bus RGB
interface mode
VSYNC / tSYNCS VSYNC/HSYNC setup time 15 - ns
HSYNC tSYNCH VSYNC/HSYNC hold time 15 - ns
tENS DE setup time 15 - ns DE
tENH DE hold time 15 - ns
tPOS Data setup time 15 - ns D[17:0]
tPDH Data hold time 15 - ns
PWDH DOTCLK high-level pulse period 15 - ns
PWDL DOTCLK low-level pulse period 15 - ns
tCYCD DOTCLK cycle time 100 - ns
DOTCLK
trgbr , trgbf DOTCLK,HSYNC,VSYNC rise/fall time - 15 ns
6-bit bus RGB
interface mode
Note: Ta = -30 to 70 °C, VDDI=1.65V to 3.3V, VCI=2.5V to 3.3V, AGND=VSS=0V
tr≦15ns
70%
30%
70%
30%
tf≦15ns
a-Si TFT LCD Single Chip Driver
240RGBx320 Resolution and 262K color ILI9341
The information contained herein is the exclusive property of ILI Technology Corp. and shall not be distributed,
reproduced, or disclosed in whole or in part without prior written permission of ILI Technology Corp.
Page 239 of 239
19 Revision History
Version No. Date Page Description
V1.00 2010/10/12 All New Created.
V1.01 2010/10/12 179 Update charge pump ratio
V1.02 2010/12/17 35,195~200 Add description of extend register command
V1.03 2010/12/20 196 Modify description of pumping
V1.04 2010/12/24 All Update extend register and OTP flow
V1.05 2010/12/27 All Update extend register
