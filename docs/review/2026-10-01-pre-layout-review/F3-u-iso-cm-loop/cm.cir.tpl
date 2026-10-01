* U-ISO common-mode loop, small-signal AC. Unit CM drive through the isolation capacitance.
* CM source: the converter's switching node referred to its input, coupling through C_iso (1100 pF typ) to PWR_GND
VCM s vinn AC 1
CISO s pg 1.1n
* input filter (C-ISO-IN 4.7u X7R, C2 100u ESR 0.34)
CIN vinp cin1 4.7u
LCIN cin1 vinn 1n
C2 vinp c2a 100u
RC2 c2a c2b 0.34
LC2 c2b vinn 10n
* CM choke between the converter's pins (vinp/vinn) and the filter side (fp/fn), or straight through
{CHOKE}
* C-ISO-Y ISO_VIN_POS to PWR_GND (ESL 1 nH), and an optional twin from ISO_VIN_NEG
CY vinp cya {CY}
LCY cya cyr 1n
RY cyr pg {YR}
CYN vinn cyb {CYN}
LCYN cyb pg 1n
* PWR_GND -> NT-UMB-MOD -> DIG_GND -> NT-DIG-MOD -> BUS_GND -> NT-AGND-MOD -> AGND_MOD (copper, ~10 nH each)
LT1 pg dg 10n
LT2 dg bgx 10n
VPROBE_STAR bgx bg 0
LT3 bg agx 10n
VPROBE_AGND agx ag 0
* -12 V entry: C3 47u electrolytic (ESR 0.7, ESL 10n) from AGND_MOD to MODULE_ANALOG_NEG12
C3 ag c3a 47u
RC3 c3a c3b 0.7
LC3 c3b n12 10n
* FB3 at ~40 mA: bead ~ 2.2 uH || 650 ohm || 1.6 pF, DCR 0.05 [MI1206K601R-10 curve]
LFB3 n12 fb3 2.2u
RFB3P n12 fb3 650
CFB3 n12 fb3 1.6p
RFB3 fb3 d3a 0.05
RD3 d3a ptc3 0.9
RPTCN ptc3 bneg {RPTC}
RD4 bneg d4a 0.4
* FB4 at ~0.22 A: ~0.85 uH
LFB4 d4a fb4 0.85u
RFB4P d4a fb4 650
CFB4 d4a fb4 1.6p
RFB4 fb4 fn 0.05
* +12 V side: L-ISO-IN 22u (SRF ~20 MHz), FB2 0.85u, D2, PTC-ISO
LISO fp liso 22u
CISOP fp liso 3p
RISOP fp liso 5k
LFB2 liso fb2 0.85u
RFB2P liso fb2 650
RFB2 fb2 d2 0.05
RD2 d2 ptci 0.4
RPTCI ptci bpos 0.2
* +12 V analog: PTC-POS12, D1, FB1 (~2.2 uH at 22 mA), C1 100u to AGND_MOD, C-LOGIC-IN 4.7u to DIG_GND, C-DEC-REG-IN 100n to AGND_MOD
RPTCP bpos d1 {RPTC}
RD1 d1 fb1 0.9
LFB1 fb1 p12 2.2u
RFB1P fb1 p12 650
C1 p12 c1a 100u
RC1 c1a c1b 0.4
LC1 c1b ag 10n
CLI p12 cli 4.7u
LCLI cli dg 2n
CDR p12 cdr 100n
LCDR cdr ag 2n
* the rack: ribbon (LRIB per conductor) to the PSU and the other modules' decoupling, returning on the ribbon's GND
LRN bneg rn {LRIB}
CRN rn rnc 100u
RCRN rnc rnd 0.1
LCRN rnd rg 20n
LRP bpos rp {LRIB}
CRP rp rpc 100u
RCRP rpc rpd 0.1
LCRP rpd rg 20n
LRG rg bgr {LRIB}
VPROBE_RACK bgr bg 0
.control
ac dec 200 100k 30meg
let iy = mag(i(LCY)+i(LCYN))
let ia = mag(i(VPROBE_AGND))
let ir = mag(i(VPROBE_RACK))
let it = mag(i(VCM))
let istar = mag(i(VPROBE_STAR))
meas ac y550 find iy at=550k
meas ac a550 find ia at=550k
meas ac r550 find ir at=550k
meas ac s550 find istar at=550k
meas ac t550 find it at=550k
meas ac y1650 find iy at=1.65meg
meas ac a1650 find ia at=1.65meg
meas ac s1650 find istar at=1.65meg
meas ac t1650 find it at=1.65meg
meas ac y5500 find iy at=5.5meg
meas ac a5500 find ia at=5.5meg
meas ac s5500 find istar at=5.5meg
meas ac t5500 find it at=5.5meg
quit
.endc
.end
