from openerp.osv import osv
from ads_product import ads_product

class product_product(osv.osv):
    """
    Add some fields to product to track synchronisation and trigger upload on write
    """
    _inherit = 'product.product'

    def write(self, cr, uid, ids, values, context=None):
        """ Call ads_upload if we edit an uploaded field """
        res = super(product_product, self).write(cr, uid, ids, values, context=context)
        if any([field for field in ads_product.uploaded_fields if field in values.keys()]):
            self.ads_upload(cr, uid, ids, context=context)
        return res

    def ads_upload_all(self, cr, uid, context=None):
        ids = self.search(cr, uid, [('x_new_ref', '!=', '')])
        self.ads_upload(cr, uid, ids, context=context)
        return True

    def ads_upload(self, cr, uid, ids, context=None):
        """ Upload product to ads server """
        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        for product_id in ids:
            product = self.browse(cr, uid, product_id, context=context)
            data = ads_product(product)
            data.upload(cr, self.pool.get('ads.manager'))
