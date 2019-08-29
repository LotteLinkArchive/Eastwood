from secrets import compare_digest
from hashlib import sha256
from quarry.net.protocol import BufferUnderrun

from eastwood.protocols.ew_protocol import EWProtocol

class InternalProxyInternalProtocol(EWProtocol):
	"""
	Handles poems from the external proxy and sends them to the minecraft server, and vice versa
	"""
	def __init__(self, factory, buff_class, handle_direction, other_factory, buffer_wait, password):
		"""
		Protocol args:
			factory: factory that made this protocol (subclass of EWFactory)
			other_factory: the other factory that communicates with this protocol (in this case an instance of MCProtocol)
			buffer_wait: amount of time to wait before sending buffered packets (in ms)
			password: password to authenticate with
		"""
		super().__init__(factory, buff_class, handle_direction, other_factory, buffer_wait, password)
		self.authed = False

	def packet_received(self, buff, name):
		"""
		Treat all packets as an auth packet until the packet has been authenticated
		"""
		if not self.authed:
			self.packet_special_auth(buff)
			return

		super().packet_received(buff, name)

	def packet_special_auth(self, buff):
		"""
		This packet does not get handled like standard packets to prevent a rogue client from abusing the check
		"""
		try:
			hashed_pass = buff.unpack_packet(self.buff_class).read()
			salt = buff.unpack_packet(self.buff_class).read()

			# Verify hashed pass with salt
			sha = sha256()
			sha.update(self.password.encode() + salt)
			my_pass = sha.digest()

			if compare_digest(hashed_pass, my_pass):
				self.authed = True
				self.logger.info("Authenticated!") # Successfully authenticated!
				return
		except BufferUnderrun:
			pass

		# Either the auth packet was not valid, or the compare was rejected, dc
		self.transport.loseConnection()

	def packet_recv_add_conn(self, buff):
		# Add a connection to InternalProxyMCClientFactory
		self.other_factory.add_connection(buff.unpack_uuid())

	def packet_recv_delete_conn(self, buff):
		# Delete uuid connection
		uuid = buff.unpack_uuid()
		try:
			self.other_factory.get_client(uuid).transport.loseConnection()
		except KeyError:
			pass # Already gone
		except AttributeError:
			del self.other_factory.uuid_dict[uuid.to_hex()] # Delete the reference if it is none