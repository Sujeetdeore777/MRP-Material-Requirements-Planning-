modulename := "simrp"
Return

^+c::
;   Type "class name", keep cusror at end
	Send, {ctrl down}{shift down}{left}{ctrl up}{shift up}^c^x
	sleep, 300
	ctc := Format("{:T}", Clipboard)
	Send,
	(
	class %ctc%(models.Model):
	_name = '%modulename%.%Clipboard%'

name = fields.Char( '%ctc%', size = 50 )
)
Return

::=fc::
	Send, {ctrl down}{shift down}{left}{ctrl up}{shift up}^c^x
	sleep, 300
	c := Trim( Clipboard )
	ctc := Format( "{:T}", c )
	Send, %c% = fields.Char( '%ctc%', size = 20 )
Return

::=fb::
	Send, {ctrl down}{shift down}{left}{ctrl up}{shift up}^c^x
	sleep, 300
	c := Trim( Clipboard )
	ctc := Format( "{:T}", c )
	Send, %c% = fields.Boolean( '%ctc%' )
Return

::=fi::
	Send, {ctrl down}{shift down}{left}{ctrl up}{shift up}^c^x
	sleep, 300
	c := Trim( Clipboard )
	ctc := Format( "{:T}", c )
	Send, %c% = fields.Integer( '%ctc%' )
Return

::=ff::
	Send, {ctrl down}{shift down}{left}{ctrl up}{shift up}^c^x
	sleep, 300
	c := Trim( Clipboard )
	ctc := Format( "{:T}", c )
	Send, %c% = fields.Float( '%ctc%', digits=(8,2) )
Return

::=ft::
	Send, {ctrl down}{shift down}{left}{ctrl up}{shift up}^c^x
	sleep, 300
	c := Trim( Clipboard )
	ctc := Format( "{:T}", c )
	Send, %c% = fields.Text( '%ctc%' )
Return

::=fs::
	Send, {ctrl down}{shift down}{left}{ctrl up}{shift up}^c^x
	sleep, 300
	c := Trim( Clipboard )
	ctc := Format( "{:T}", c )
	Send, 
	(
	%c% = fields.Selection( [
		( '', '' ),
( '', '' ),
], '%ctc%' )
)
Return

::=fd::
	Send, {ctrl down}{shift down}{left}{ctrl up}{shift up}^c^x
	sleep, 300
	c := Trim( Clipboard )
	ctc := Format( "{:T}", c )
	Send, %c% = fields.Date( '%ctc%', default=lambda self: fields.Date.today() )
Return

::=fdt::
	Send, {ctrl down}{shift down}{left}{ctrl up}{shift up}^c^x
	sleep, 300
	c := Trim( Clipboard )
	ctc := Format( "{:T}", c )
	Send, %c% = fields.Datetime( '%ctc%', default=lambda self: fields.Datetime.now() )
Return

::=fmo::
	c := Trim( Clipboard )
	ctc := Format( "{:T}", c )
	Send, %c%_ = fields.Many2one( '%modulename%.%c%', '%ctc%', domain=[('state', '=', 'a')] )
Return

::=fom::
	c := Trim( Clipboard )
	ctc := Format( "{:T}", c )
	Send, %c%_s = fields.One2many( '%modulename%.%c%', 'thisclassM2o_', '%ctc%', domain=[('state', '=', 'a')] )
Return

:?:,rq::, required = True{del}
:?:,ro::, readonly = True{del}
:?:,dt::, default=datetime.date.today(){del}

^+f::
	c := Trim( Clipboard )
	Send,  , compute='_x%c%', store=True{end}{enter}
	Send,
	(
    @api.multi

@api.depends('','')
def _x%c%(self):
    for o in self:
	r = ''
	o.%c% = ''
)
Return

^+x::
	Send,<field name="{ctrl down}{right}{ctrl up}{left}"/>{shift down}{end}{shift up}{del}{right}{ctrl down}{right}{ctrl up}
Return

^+d::
	Send,'{ctrl down}{right}{ctrl up}{left}': self.,{shift down}{end}{shift up}{del}{right}{ctrl down}{right}{ctrl up}
Return

^!+x::
	Send, {ctrl down}{shift down}{left}{ctrl up}{shift up}^c^x
	sleep, 300
	c := Trim( Clipboard )
	ctc := Format( "{:T}", c )
	Send,^n
	sleep, 500
	Send,
	(
<?xml version="1.0" encoding="utf-8"?>
<odoo>

<record id="%c%_actionname_action" model="ir.actions.act_window">
<field name="name">namenotdisplayed</field>
<field name="res_model">%modulename%.wizardname</field>
<field name="view_type">form</field>
<field name="view_mode">form</field>
<field name="target">new</field>
</record>

<record id="%modulename%_%c%_form" model="ir.ui.view">
<field name="name">%modulename%.%c%.form</field>
<field name="model">%modulename%.%c%</field>
<field name="arch" type="xml">
<form>
<header>
<button name="approve" type="object" class="oe_stat_button" icon="fa-check-circle" string="Approve" attrs="{{}'invisible': [('state','!=',('s'))]{}}" groups="simrp.group_simrp_ceo" />
<button name="draft" type="object" class="oe_stat_button" icon="fa-undo" string="Re-open" attrs="{{}'invisible': [('state','=',('d'))]{}}" groups="simrp.group_simrp_works" />
<button name="submit" type="object" class="oe_stat_button" icon="fa-folder-open" string="Submit for Approval" attrs="{{}'invisible': [('state','!=',('d'))]{}}" groups="simrp.group_simrp_user" />
<field name="state" widget="statusbar"/>
</header>
<sheet string="%ctc%">

<field name="id" invisible="1"/>
<div class="oe_button_box" name="button_box">
<button name="`%(%c%_actionname_action)d" type="action" class="oe_stat_button" icon="fa-fast-forward" string="actionbuttontext" attrs="{{}'invisible': [('state','=',('c'))]{}}" groups="%modulename%.group_%modulename%_user" context="{{}'default_%c%_':id{}}"/>
</div>

<div class="oe_title pr-0">
<h1 class="d-flex flex-row ">
<field name="name" />
</h1>
</div>					

<group>
<group>
</group>
<group>
</group>
</group>

<notebook>
<page name="p1" string="">
<group col="4">
<field name="" nolabel="1" colspan="4">								
<tree>
</tree>
</field>
</group>
</page>
<page name="Info" string="">
<group col="4">
</group>
</page>
</notebook>
</sheet>
</form>
</field>
</record>

<record id="%modulename%_%c%_tree" model="ir.ui.view">
<field name="name">%modulename%.%c%.tree</field>
<field name="model">%modulename%.%c%</field>
<field name="arch" type="xml">
<tree decoration-success="state=='a'" >
</tree>
</field>
</record>

<record id="%modulename%_%c%_search" model="ir.ui.view">
<field name="name">%modulename%.%c%.search</field>
<field name="model">%modulename%.%c%</field>
<field name="arch" type="xml">
<search>
</search>
</field>
</record>

<record id="%modulename%_%c%_action" model="ir.actions.act_window">
<field name="name">%ctc%</field>
<field name="res_model">%modulename%.%c%</field>
<field name="view_mode">tree,form</field>
</record>

<menuitem action="%modulename%_%c%_action" id="%modulename%_%c%_menu" name="%ctc%" parent="%modulename%_menu" sequence="" groups="group_%modulename%_user"/>

%modulename%_%c%_user,%modulename%_%c%_user,model_%modulename%_%c%,%modulename%.group_%modulename%_user,1,0,0,0
%modulename%_%c%_works,%modulename%_%c%_works,model_%modulename%_%c%,%modulename%.group_%modulename%_works,1,1,1,0
%modulename%_%c%_ceo,%modulename%_%c%_ceo,model_%modulename%_%c%,%modulename%.group_%modulename%_ceo,1,1,1,1

        '%c%.xml',

</odoo>
{ctrl down}{home}{ctrl up}
)
	Send,{alt down}f{alt up}a
	sleep, 1000
	Send,%c%.xml{enter}
Return

::=/pg::
	c := Trim( Clipboard )
	Send,
(
%modulename%_%c%_user,%modulename%_%c%_user,model_%modulename%_%c%,%modulename%.group_%modulename%_user,1,0,0,0
%modulename%_%c%_works,%modulename%_%c%_works,model_%modulename%_%c%,%modulename%.group_%modulename%_works,1,1,1,0
%modulename%_%c%_ceo,%modulename%_%c%_ceo,model_%modulename%_%c%,%modulename%.group_%modulename%_ceo,1,1,1,1
)
Return

::=/pg1::
	c := Trim( Clipboard )
	Send,
(
%modulename%_%c%_member,%modulename%_%c%_member,model_%modulename%_%c%,%modulename%.group_%modulename%_member,1,0,0,0
%modulename%_%c%_sessionadmin,%modulename%_%c%_sessionadmin,model_%modulename%_%c%,%modulename%.group_%modulename%_sessionadmin,1,0,0,0
%modulename%_%c%_dataadmin,%modulename%_%c%_dataadmin,model_%modulename%_%c%,%modulename%.group_%modulename%_dataadmin,1,1,1,1
%modulename%_%c%_memberadmin,%modulename%_%c%_memberadmin,model_%modulename%_%c%,%modulename%.group_%modulename%_memberadmin,1,1,1,1
)
Return


::=/sn::
	c := Trim( Clipboard )
	ctc := Format( "{:T}", c )
	Send,
(
<record id="seq_%c%" model="ir.sequence">
<field name="name">%ctc% sequence</field>
<field name="code">%modulename%.%c%</field>
<field name="prefix"></field>
<field eval="1" name="number_next"/>
<field eval="1" name="number_increment"/>
<field eval="False" name="use_date_range"/>
<field eval="False" name="company_id"/>
<field name="padding">6</field>
</record>
@api.model

def create(self, vals):
vals['name'] = self.env['ir.sequence'].next_by_code('%modulename%.%c%')
return super(%ctc%, self).create(vals)
)
Return


::=/ab::
	c := Trim( Clipboard )
	ctc := Format( "{:T}", c )
	Send,
	(
<record id="%c%_actionname_action" model="ir.actions.act_window">
<field name="name">namenotdisplayed</field>
<field name="res_model">%modulename%.wizardname</field>
<field name="view_type">form</field>
<field name="view_mode">form</field>
<field name="target">new</field>
</record>

<field name="id" invisible="1"/>
<div class="oe_button_box" name="button_box">
<button name="`%(%c%_actionname_action)d" type="action" class="oe_stat_button" icon="fa-fast-forward" string="actionbuttontext" attrs="{{}'invisible': [('state','=',('c'))]{}}" groups="%modulename%.group_%modulename%_user" context="{{}'default_%c%_':id{}}"/>
</div>
)
Return

::=/df::
	Send, [ ( '', '=', '' ) ]
Return


^!+r::
	Send,^s
	Reload
Return
