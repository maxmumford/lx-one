from ftplib import error_perm

from openerp.tools.translate import _
from openerp.osv import osv, fields

from lx_sales_order import lx_sales_order
from lx_purchase_order import lx_purchase_order
from oe_lx import oe_lx

def all_assigned(picking_obj, cr, ids):
    """ Returns true if all pickings have state 'assigned' """
    for picking in picking_obj.read(cr, 1, ids, ['state']):
        if picking['state'] != 'assigned':
            return False
    return True

def pick_cancel_manuel(obj, cr, uid, ids, context=None):
    """
    Called when manually cancelling a picking.  
    If picking was uploaded and file still exists on the server, delete it and cancel the picking. 
    If it no longer exists on the server, raise an error.
    If picking was never uploaded, just cancel the picking. 
    """
    
    def cannot_cancel():
        """ Raise OE exception saying picking was already imported and cannot be canceled """
        raise osv.except_osv(_("Cannot Cancel Delivery Order"), _("The delivery order has already been imported by LX1 so it cannot be canceled anymore"))
    
    for picking in obj.browse(cr, uid, ids):
        picking_id = picking.id
         
        # Was it uploaded?
        if picking.lx_file_name:
            with obj.pool['lx.manager'].connection(cr) as conn:
                try:
                    # Try to delete the file from the server
                    conn.delete_data(picking.lx_file_name)
                    
                    # Reset the sent flah and file name, then cancel
                    obj.write(cr, uid, picking_id, {'lx_sent': False, 'lx_file_name': False})
                    obj.action_cancel(cr, uid, [picking_id], context=context)
                except error_perm, e:
                    # Cannot delete the file so it's already been imported to LX1. Raise an error
                    cannot_cancel()
        else:
            # Never uploaded to cancel picking
            obj.action_cancel(cr, uid, [picking_id], context=context)
    return True

class stock_picking(oe_lx, osv.osv):
    """
    Inherit the stock.picking to prevent manual processing.

    If LX1 does not have stock to fulfill an order, they cancel the order and we have to re-upload
    it with a different BL and SO number. To handle this we cancel the BL, duplicate it (incrementing
    the name automatically) then append the value of the lx_send_number field to the end of the original
    SO name.
    """

    _inherit = 'stock.picking'

    def action_process(self, cr, uid, ids, context=None):
        if all_assigned(self, cr, ids):
            raise osv.except_osv(_('Cannot Process Manually'), _("The picking should be processed in the LX1 system. It will then be automatically synchronized to OpenERP."))
        else:
            super(stock_picking, self).action_process(cr, uid, ids, context=context)

class stock_picking_in(oe_lx, osv.osv):
    """ Inherit the stock.picking.in to prevent manual processing and cancellation after lx upload """

    _inherit = 'stock.picking.in'

    def cancel_manuel(self, cr, uid, ids, context=None):
        """ Manual cancellation by user on form view """
        return pick_cancel_manuel(self, cr, uid, ids, context=context)

    def action_disallow_invoicing(self, cr, uid, ids, context=None):
        """ When picking is received automatically it is set as invoicable. Add option to make non invoicable """
        self.write(cr, uid, ids, {'invoice_state': 'none'})

    def lx_manuel_upload(self, cr, uid, ids, context=None):
        """ 
        Upload this picking to LX1. If a file_name already exists on the picking, try to delete
        it from the server, then upload again and set new file_name. 
        """
        for picking_id in ids:
            picking = self.browse(cr, uid, picking_id, context=context)

            # make sure state is correct
            if not picking.state == 'assigned':
                continue

            # try to delete existing file
            if picking.lx_file_name:
                with self.pool['lx.manager'].connection(cr) as conn:
                    try:
                        conn.delete_data(picking.lx_file_name)
                    except error_perm, e:
                        pass
            
            # upload file
            data = lx_purchase_order(picking)
            data.upload(cr, self.pool.get('lx.manager'))
        return True

class stock_picking_out(oe_lx, osv.osv):
    """ Inherit the stock.picking.in to prevent manual processing and cancellation after LX1 upload """

    _inherit = 'stock.picking.out'
    
    def cancel_manuel(self, cr, uid, ids, context=None):
        """ Manual cancellation by user on form view """
        return pick_cancel_manuel(self, cr, uid, ids, context=context)

    def lx_manuel_upload(self, cr, uid, ids, context=None):
        """ Upload this picking to LX1 """
        for picking_id in ids:
            picking = self.browse(cr, uid, picking_id, context=context)

            # make sure state is correct
            if not picking.state == 'assigned':
                continue

            # try to delete existing file
            if picking.lx_file_name:
                with self.pool['lx.manager'].connection(cr) as conn:
                    try:
                        conn.delete_data(picking.lx_file_name)
                    except error_perm, e:
                        pass
            
            # upload file
            data = lx_sales_order(picking)
            data.upload(cr, self.pool.get('lx.manager'))
        return True
