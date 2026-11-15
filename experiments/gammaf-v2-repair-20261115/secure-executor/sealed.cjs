'use strict';
const crypto=require('node:crypto');
function openEnvelope(envelope,privatePem,ownPublic,expected){
 if(envelope.protocol!=='rfdl-gammaf-sealed-v1'||envelope.recipient_public_spki_b64url!==ownPublic)throw new Error('Credential recipient mismatch');
 const aad=Buffer.from(envelope.aad_b64,'base64'),ctx=JSON.parse(aad.toString('utf8'));
 if(Object.keys(ctx).length!==Object.keys(expected).length)throw new Error('Unexpected credential context fields');
 for(const[k,v]of Object.entries(expected))if(ctx[k]!==v)throw new Error('Credential context mismatch: '+k);
 const salt=Buffer.from(envelope.salt_b64,'base64'),nonce=Buffer.from(envelope.nonce_b64,'base64'),ciphertext=Buffer.from(envelope.ciphertext_b64,'base64');
 if(salt.length!==32||nonce.length!==12||ciphertext.length<17||ciphertext.length>4096)throw new Error('Invalid authenticated envelope');
 const peer=crypto.createPublicKey({key:Buffer.from(envelope.sender_public_spki_b64url,'base64url'),format:'der',type:'spki'});
 if(peer.asymmetricKeyType!=='x25519')throw new Error('Unsupported sender key');
 const shared=crypto.diffieHellman({privateKey:crypto.createPrivateKey(privatePem),publicKey:peer});
 const info=Buffer.concat([Buffer.from('rfdl-gammaf-sealed-v1\0'),aad]);
 const derived=Buffer.from(crypto.hkdfSync('sha256',shared,salt,info,32));
 const decipher=crypto.createDecipheriv('aes-256-gcm',derived,nonce,{authTagLength:16});
 decipher.setAAD(aad);decipher.setAuthTag(ciphertext.subarray(-16));
 const plain=Buffer.concat([decipher.update(ciphertext.subarray(0,-16)),decipher.final()]);
 shared.fill(0);derived.fill(0);return plain;
}
module.exports={openEnvelope};
