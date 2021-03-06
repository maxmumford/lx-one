from copy import copy
from collections import OrderedDict

from openerp import osv
from openerp.tools.translate import _

from lx_data import lx_data

class lx_product(lx_data):

	object_type = ['ARTI']
	message_identifier = 'OpenErpItemCreate'

	required_fields = [
		'name',
		'ean13',
		'uom_id',
	]

	def extract(self, product):
		"""
		Takes a product browse_record and extracts the
		appropriate data into self.data

		@param browse_record(product.product) product: the product browse record object
		"""
		
		self.data = OrderedDict([
		('ItemMasterCreate', OrderedDict([
				('Client', 'pvszmd'),
				('Item', product.ean13),
				('Description', product.name),
				('QuantityProperties', OrderedDict([
					('StandardUOM', 'STCK'),
				])),
			])
		)])
