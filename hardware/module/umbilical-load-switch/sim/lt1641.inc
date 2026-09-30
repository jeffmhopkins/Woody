* LT1641-1, BEHAVIOURAL, built from the banked datasheet (datasheets/discrete-and-power/
* LT1641.pdf, 164112fc) - no vendor model is banked (fragment R29 records it BLOCKED).
* Pins in the netlist's order: VCC SENSE GATE FB TIMER ON PWRGD GND. Each law and number
* is a parameter of the subcircuit, set per corner by sims.yaml, with its page there:
*   foldback: V(VCC)-V(SENSE) limited to vlo at V_FB = 0, linear to vhi at V_FB = 0.5 V,
*     flat above (p.5, p.8, Figure 7)
*   GATE: pulled up by igate (I_GATEUP) to VCC + dvg (dVGATE); pulled down by the
*     current-limit amplifier, a transconductance gm [NOT IN THE DATASHEET: an
*     assumption, large enough that the regulation error is under 1 mV] limited to
*     70 mA (I_GATEDN typ); pulled to GND at 70 mA when the fault latch is set
*   TIMER: 80 uA-class pull-up (itup) while the current limit is active, and a 3 uA-class
*     pull-down (itdn) always, which is how the datasheet's "77 uA/C_TIMER" arises (p.8);
*     1.233 V sets the fault latch (-1: latched until ON is cycled or power removed, p.5)
*   "current limit active": the amplifier is sinking more than half of I_GATEUP
* ON and PWRGD are not modelled: ON is held high (the UVLO divider is the page's open
* item), and PWRGD drives nothing (netlist: an external endpoint).
.subckt LT1641B vcc sense gate fb timer on pwrgd gnd
+ vlo=12m vhi=47m igate=10u dvg=10 gm=0.1 itup=80u itdn=3u
* the foldback law, and the amplifier's pull-down
Blim lim gnd V = {vlo} + ({vhi}-{vlo})*min(max(V(fb,gnd),0),0.5)/0.5
Bamp gate gnd I = min(max({gm}*(V(vcc,sense)-V(lim,gnd)), 0), 70m)
* the charge pump, clamped at VCC + dvg
Bpump vcc gate I = {igate}*0.5*(1 - tanh((V(gate,vcc)-{dvg})/0.05)) + 0*V(latch)
* active when the amplifier sinks more than half of I_GATEUP
Bact act gnd V = 0.5*(1 + tanh(({gm}*(V(vcc,sense)-V(lim,gnd)) - 0.5*{igate})/(0.1*{igate})))
Ract act gnd 1G
* TIMER
Btup vcc timer I = {itup}*V(act,gnd)*(V(latch,gnd) > 0.5 ? 0 : 1)
Btdn timer gnd I = {itdn}*tanh(max(V(timer,gnd),0)/0.01)
* the fault latch: set at 1.233 V, never cleared inside a run
Blset gnd latch I = ((V(timer,gnd) > 1.233 || V(latch,gnd) > 0.5) ? 1m : 0)*(1.001 - V(latch,gnd))
Clatch latch gnd 1n
Rlatch latch gnd 1G
Bfault gate gnd I = (V(latch,gnd) > 0.5 ? 70m : 0)*tanh(max(V(gate,gnd),0)/0.1)
Ron on gnd 1G
Rpg pwrgd gnd 1G
.ends
