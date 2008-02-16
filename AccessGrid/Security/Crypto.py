#!/usr/bin/python

from M2Crypto import EVP
import cStringIO

def cipher_filter( cipher, inf, outf):
    while 1:
        buf=inf.read()
        if not buf:
            break
        outf.write(cipher.update(buf))
    outf.write(cipher.final())
    return outf.getvalue()

def encrypt(data,key,iv='iv',ciph='bf_cbc'):
    k=EVP.Cipher(alg=ciph, key=key, iv=iv, op=1)
    pbuf=cStringIO.StringIO(data)
    cbuf=cStringIO.StringIO()
    ciphertext = cipher_filter(k, pbuf, cbuf)
    pbuf.close()
    cbuf.close()
    return ciphertext
    
def decrypt(data,key,iv='iv',ciph='bf_cbc'):
    j=EVP.Cipher(alg=ciph, key=key, iv=iv, op=0)
    pbuf=cStringIO.StringIO()
    cbuf=cStringIO.StringIO(data)
    plaintext=cipher_filter(j, cbuf, pbuf)
    pbuf.close()
    cbuf.close()
    return plaintext
    
    
if __name__ == '__main__':
    import sys
    import base64
    data = sys.argv[1]
    key = sys.argv[2]
    
    print 'data = ', data
    e = encrypt(data,key)
    print 'encrypted data = ', e, base64.encodestring(e)
    d = decrypt(e,key)
    print 'decrypted data = ', d
    
    assert(d == data)

