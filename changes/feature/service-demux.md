Serve RPC on the application socket. Bind ServiceDemux and the injected-transport
constructors, and register each configured service on a demux attached to the
server transport instead of a second ephemeral RPC socket.
