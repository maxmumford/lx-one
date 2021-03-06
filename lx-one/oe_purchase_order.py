from openerp.osv import osv

from lx_purchase_order import lx_purchase_order
from oe_lx import oe_lx

class stock_picking(oe_lx, osv.osv):
    """
    Inherit the stock.picking object to trigger upload of PO pickings
    """
    _inherit = 'stock.picking'
    
    def action_assign_wkf(self, cr, uid, ids, context=None):
        """ Upload picking to LX1 """
        res = super(stock_picking, self).action_assign_wkf(cr, uid, ids, context=context)
    
        for picking_id in ids:
            picking = self.browse(cr, 1, picking_id, context=context)

            if picking.type.lower() == 'in':
                self.upload(cr, 1, picking, lx_purchase_order)
                    
        return res
