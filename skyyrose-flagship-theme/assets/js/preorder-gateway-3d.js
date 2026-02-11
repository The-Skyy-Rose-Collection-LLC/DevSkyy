import*as THREE from'three';
import{OrbitControls}from'three/addons/controls/OrbitControls.js';
import{EffectComposer}from'three/addons/postprocessing/EffectComposer.js';
import{RenderPass}from'three/addons/postprocessing/RenderPass.js';
import{UnrealBloomPass}from'three/addons/postprocessing/UnrealBloomPass.js';
import{ShaderPass}from'three/addons/postprocessing/ShaderPass.js';
import{OutputPass}from'three/addons/postprocessing/OutputPass.js';

/* ── ALL PRODUCTS FROM 3 COLLECTIONS ── */
const COLLECTIONS={
'black-rose':{name:'BLACK ROSE',accent:'#DC143C',items:[
{id:'br-001',name:'Thorn Hoodie',price:185,sku:'SR-BR-THORN-H',sizes:['S','M','L','XL','XXL'],desc:'Heavyweight 380gsm cotton fleece with gothic thorn embroidery. Oversized fit, hidden rose zipper pulls.',col:'black-rose'},
{id:'br-002',name:'Midnight Bomber',price:295,sku:'SR-BR-MID-J',sizes:['S','M','L','XL'],desc:'Premium satin bomber with hand-painted black rose motifs. Quilted interior, crimson contrast stitching.',col:'black-rose'},
{id:'br-003',name:'Gothic Tee',price:75,sku:'SR-BR-GOTH-T',sizes:['S','M','L','XL','XXL'],desc:'300gsm Supima cotton. Screen-printed thorn crown graphic with reflective ink detail.',col:'black-rose'},
{id:'br-004',name:'Chain Cargo',price:145,sku:'SR-BR-CHAIN-C',sizes:['28','30','32','34','36'],desc:'Relaxed cargo with detachable silver chain hardware. Waxed cotton blend in obsidian.',col:'black-rose'}]},
'love-hurts':{name:'LOVE HURTS',accent:'#E91E63',items:[
{id:'lh-001',name:'Heartbreak Hoodie',price:195,sku:'SR-LH-HB-H',sizes:['S','M','L','XL','XXL'],desc:'Premium French terry with hand-distressed heart patch. Barbed wire embroidery along sleeves.',col:'love-hurts'},
{id:'lh-002',name:'Tears Jacket',price:325,sku:'SR-LH-TEARS-J',sizes:['S','M','L','XL'],desc:'Full-grain leather biker jacket with thorn-wrapped heart hardware. Burgundy satin interior.',col:'love-hurts'},
{id:'lh-003',name:'Wounded Tee',price:85,sku:'SR-LH-WOUND-T',sizes:['S','M','L','XL','XXL'],desc:'Oversized boxy tee with cracked heart screenprint. Vintage acid wash, raw hem.',col:'love-hurts'},
{id:'lh-004',name:'Scar Pants',price:165,sku:'SR-LH-SCAR-P',sizes:['28','30','32','34','36'],desc:'Tailored wide-leg trouser with decorative scar stitching. Burgundy racing stripe.',col:'love-hurts'}]},
'signature':{name:'SIGNATURE',accent:'#D4AF37',items:[
{id:'sg-001',name:'Foundation Blazer',price:395,sku:'SR-SG-BLAZ',sizes:['S','M','L','XL'],desc:'Italian wool-blend blazer with rose-gold hardware. Signature Oakland-inspired lining.',col:'signature'},
{id:'sg-002',name:'Essential Trouser',price:245,sku:'SR-SG-TROU',sizes:['28','30','32','34','36'],desc:'Tailored wide-leg in premium wool. Gold-foil branding on interior waistband.',col:'signature'},
{id:'sg-003',name:'Luxury Tee',price:125,sku:'SR-SG-TEE',sizes:['S','M','L','XL','XXL'],desc:'400gsm Supima cotton with metallic rose-gold embroidered crest. Relaxed fit.',col:'signature'},
{id:'sg-004',name:'Heritage Coat',price:595,sku:'SR-SG-COAT',sizes:['S','M','L','XL'],desc:'Double-breasted cashmere-blend overcoat. Rose-gold closure hardware, satin interior.',col:'signature'},
{id:'sg-005',name:'Classic Oxford',price:175,sku:'SR-SG-OXFD',sizes:['S','M','L','XL','XXL'],desc:'Premium poplin with signature rose-gold collar stays. Mother-of-pearl buttons.',col:'signature'}]}
};
const ALL_PRODUCTS=Object.values(COLLECTIONS).flatMap(c=>c.items);
let activeCollection='all';

/* ── 3D SCENE ── */
let scene,camera,renderer,composer,controls,clock,particles;
const cart=[];let currentProduct=null;let selectedSize=null;

function init(){
clock=new THREE.Clock();scene=new THREE.Scene();scene.fog=new THREE.FogExp2(0x030006,.008);scene.background=new THREE.Color(0x020004);
camera=new THREE.PerspectiveCamera(50,innerWidth/innerHeight,.1,120);camera.position.set(0,4,14);
renderer=new THREE.WebGLRenderer({canvas:document.getElementById('scene'),antialias:true,powerPreference:'high-performance'});
renderer.setSize(innerWidth,innerHeight);renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=.85;
renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.04;
controls.enablePan=false;controls.maxPolarAngle=Math.PI*.5;controls.minDistance=6;controls.maxDistance=25;
controls.autoRotate=true;controls.autoRotateSpeed=.06;controls.target.set(0,1.5,0);
buildScene();buildPost();
window.addEventListener('resize',onResize);renderer.setAnimationLoop(loop);simulateLoading();}

function buildScene(){
/* Floor - reflective obsidian */
const floorGeo=new THREE.PlaneGeometry(60,60,60,60);const fp=floorGeo.attributes.position;const fc=new Float32Array(fp.count*3);
for(let i=0;i<fp.count;i++){const x=Math.floor((fp.getX(i)+30)/3),z=Math.floor((fp.getY(i)+30)/3);
const dark=(x+z)%2===0;const c=dark?new THREE.Color(0x060308):new THREE.Color(0x0a0510);
fc[i*3]=c.r;fc[i*3+1]=c.g;fc[i*3+2]=c.b;}
floorGeo.setAttribute('color',new THREE.BufferAttribute(fc,3));
const floor=new THREE.Mesh(floorGeo,new THREE.MeshStandardMaterial({vertexColors:true,metalness:.9,roughness:.15}));
floor.rotation.x=-Math.PI/2;floor.receiveShadow=true;scene.add(floor);

/* Three collection portals - triangular arrangement */
const portalColors=[0xDC143C,0xE91E63,0xD4AF37];
const portalPositions=[[-5,0,-3],[5,0,-3],[0,0,4]];
const portalNames=['BLACK ROSE','LOVE HURTS','SIGNATURE'];

for(let i=0;i<3;i++){const g=new THREE.Group();g.position.set(...portalPositions[i]);
/* Portal arch */
const archCurve=new THREE.CatmullRomCurve3([new THREE.Vector3(-1.2,0,0),new THREE.Vector3(-1.2,3.5,0),new THREE.Vector3(-.6,4.8,0),new THREE.Vector3(0,5.2,0),new THREE.Vector3(.6,4.8,0),new THREE.Vector3(1.2,3.5,0),new THREE.Vector3(1.2,0,0)]);
const archMat=new THREE.MeshStandardMaterial({color:portalColors[i],metalness:.8,roughness:.2,emissive:portalColors[i],emissiveIntensity:.15});
g.add(new THREE.Mesh(new THREE.TubeGeometry(archCurve,24,.08,8,false),archMat));
/* Inner glow plane */
const glowMat=new THREE.MeshBasicMaterial({color:portalColors[i],transparent:true,opacity:.04,side:THREE.DoubleSide});
const glowGeo=new THREE.PlaneGeometry(2.2,5);const glow=new THREE.Mesh(glowGeo,glowMat);glow.position.y=2.5;g.add(glow);
/* Portal light */
const pl=new THREE.PointLight(portalColors[i],.8,8);pl.position.set(0,2.5,1);g.add(pl);
/* Floating symbol above */
const sym=new THREE.Mesh(new THREE.OctahedronGeometry(.25,0),new THREE.MeshStandardMaterial({color:portalColors[i],metalness:.9,roughness:.1,emissive:portalColors[i],emissiveIntensity:.3}));
sym.position.y=6;sym.userData.float={speed:.4+i*.1,offset:i*2,baseY:6,rotSpeed:.8};g.add(sym);
/* Base platform */
const base=new THREE.Mesh(new THREE.CylinderGeometry(1.5,1.8,.15,6),new THREE.MeshStandardMaterial({color:portalColors[i],metalness:.85,roughness:.15,transparent:true,opacity:.3}));
g.add(base);
g.userData.portal={color:portalColors[i],index:i};scene.add(g);}

/* Central SkyyRose monolith */
const monoG=new THREE.Group();monoG.position.set(0,0,0);
const monolith=new THREE.Mesh(new THREE.BoxGeometry(.6,4,.1),new THREE.MeshStandardMaterial({color:0x111118,metalness:.95,roughness:.05}));
monolith.position.y=2;monoG.add(monolith);
/* Gold edges */
const edgeMat=new THREE.MeshBasicMaterial({color:0xD4AF37});
[[-0.3,0],[0.3,0]].forEach(([x])=>{const e=new THREE.Mesh(new THREE.BoxGeometry(.01,4,.12),edgeMat);e.position.set(x,2,0);monoG.add(e);});
/* Crown ornament */
const crown=new THREE.Mesh(new THREE.OctahedronGeometry(.2,1),new THREE.MeshStandardMaterial({color:0xD4AF37,metalness:.95,roughness:.05,emissive:0xD4AF37,emissiveIntensity:.2}));
crown.position.y=4.3;crown.userData.float={speed:.5,offset:0,baseY:4.3,rotSpeed:1};monoG.add(crown);
monoG.userData.core=true;scene.add(monoG);

/* Connecting energy beams between portals */
for(let i=0;i<3;i++){const j=(i+1)%3;
const start=new THREE.Vector3(...portalPositions[i]);const end=new THREE.Vector3(...portalPositions[j]);
start.y=.5;end.y=.5;
const curve=new THREE.CatmullRomCurve3([start,new THREE.Vector3((start.x+end.x)/2,1.5,(start.z+end.z)/2),end]);
const beam=new THREE.Mesh(new THREE.TubeGeometry(curve,20,.01,4,false),new THREE.MeshBasicMaterial({color:0xB76E79,transparent:true,opacity:.15}));
scene.add(beam);}

/* Floating wireframe geometry field */
for(let i=0;i<15;i++){const a=Math.random()*Math.PI*2,r=5+Math.random()*8;
const geos=[new THREE.OctahedronGeometry(.2+Math.random()*.15,0),new THREE.TetrahedronGeometry(.2+Math.random()*.15,0),new THREE.IcosahedronGeometry(.15+Math.random()*.1,0)];
const colors=[0xDC143C,0xE91E63,0xD4AF37,0xB76E79];
const m=new THREE.Mesh(geos[i%3],new THREE.MeshBasicMaterial({color:colors[i%4],wireframe:true,transparent:true,opacity:.15+Math.random()*.1}));
m.position.set(Math.cos(a)*r,2+Math.random()*6,Math.sin(a)*r);
m.userData.float={speed:.15+Math.random()*.3,offset:Math.random()*Math.PI*2,baseY:m.position.y,rotSpeed:.3+Math.random()*.6};
scene.add(m);}

/* Rose-gold orbital rings */
for(let i=0;i<4;i++){const t=new THREE.Mesh(new THREE.TorusGeometry(3+i*1.2,.008,8,64),new THREE.MeshBasicMaterial({color:0xB76E79,transparent:true,opacity:.12-.02*i}));
t.position.y=4;t.rotation.x=Math.PI/3+i*.2;t.rotation.z=i*.4;t.userData.ringSpeed=.04+i*.015;scene.add(t);}

/* Particles - tri-color */
const pCnt=6000;const pGe=new THREE.BufferGeometry();const pP=new Float32Array(pCnt*3),pC=new Float32Array(pCnt*3);
for(let i=0;i<pCnt;i++){pP[i*3]=(Math.random()-.5)*35;pP[i*3+1]=Math.random()*15;pP[i*3+2]=(Math.random()-.5)*35;
const colors=[new THREE.Color(0xDC143C),new THREE.Color(0xE91E63),new THREE.Color(0xD4AF37),new THREE.Color(0xB76E79)];
const c=colors[Math.floor(Math.random()*4)];pC[i*3]=c.r;pC[i*3+1]=c.g;pC[i*3+2]=c.b;}
pGe.setAttribute('position',new THREE.BufferAttribute(pP,3));pGe.setAttribute('color',new THREE.BufferAttribute(pC,3));
particles=new THREE.Points(pGe,new THREE.PointsMaterial({size:.04,vertexColors:true,transparent:true,opacity:.35,blending:THREE.AdditiveBlending,depthWrite:false}));
scene.add(particles);

/* Lighting */
scene.add(new THREE.AmbientLight(0x0a0510,.25));
const cl=new THREE.PointLight(0xB76E79,1.5,20);cl.position.set(0,1,0);cl.castShadow=true;cl.shadow.mapSize.set(1024,1024);scene.add(cl);
scene.add(Object.assign(new THREE.DirectionalLight(0x4a2060,.2),{position:new THREE.Vector3(-5,12,5)}));
scene.add(Object.assign(new THREE.PointLight(0xDC143C,.6,12),{position:new THREE.Vector3(-6,4,-4)}));
scene.add(Object.assign(new THREE.PointLight(0xE91E63,.6,12),{position:new THREE.Vector3(6,4,-4)}));
scene.add(Object.assign(new THREE.PointLight(0xD4AF37,.6,12),{position:new THREE.Vector3(0,5,5)}));
}

function buildPost(){const rt=new THREE.WebGLRenderTarget(innerWidth,innerHeight,{type:THREE.HalfFloatType});
composer=new EffectComposer(renderer,rt);composer.addPass(new RenderPass(scene,camera));
composer.addPass(new UnrealBloomPass(new THREE.Vector2(innerWidth,innerHeight),1.3,.5,.82));
composer.addPass(new ShaderPass({uniforms:{tDiffuse:{value:null},amount:{value:.001}},vertexShader:'varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',fragmentShader:'uniform sampler2D tDiffuse;uniform float amount;varying vec2 vUv;void main(){vec2 d=amount*(vUv-.5);gl_FragColor=vec4(texture2D(tDiffuse,vUv+d).r,texture2D(tDiffuse,vUv).g,texture2D(tDiffuse,vUv-d).b,1.);}'}));
composer.addPass(new ShaderPass({uniforms:{tDiffuse:{value:null},darkness:{value:1.0},offset:{value:1.0}},vertexShader:'varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',fragmentShader:'uniform sampler2D tDiffuse;uniform float darkness;uniform float offset;varying vec2 vUv;void main(){vec4 c=texture2D(tDiffuse,vUv);vec2 u=(vUv-.5)*2.;gl_FragColor=vec4(c.rgb*clamp(1.-dot(u,u)*darkness+offset,0.,1.),c.a);}'}));
composer.addPass(new OutputPass());}

/* ── UI LOGIC ── */
function filterCollection(col){
activeCollection=col;
document.querySelectorAll('.col-tab').forEach(t=>t.classList.toggle('active',t.dataset.col===col));
renderProducts();
}window.filterCollection=filterCollection;

function renderProducts(){
const items=activeCollection==='all'?ALL_PRODUCTS:COLLECTIONS[activeCollection].items;
const grid=document.getElementById('productGrid');
grid.innerHTML=items.map(p=>{
const accent=COLLECTIONS[p.col].accent;
return '<div class="product-card" onclick="openModal(\''+p.id+'\')" style="--accent:'+accent+'"><div class="pc-image"><div class="pc-badge">'+COLLECTIONS[p.col].name+'</div></div><div class="pc-info"><div class="pc-name">'+p.name+'</div><div class="pc-price">$'+p.price+'</div></div><div class="pc-hover">Pre-Order Now</div></div>';}).join('');
document.getElementById('itemCount').textContent=items.length+' Pieces';
}

function openModal(id){
currentProduct=ALL_PRODUCTS.find(p=>p.id===id);if(!currentProduct)return;selectedSize=null;
const accent=COLLECTIONS[currentProduct.col].accent;
document.getElementById('modalName').textContent=currentProduct.name;
document.getElementById('modalPrice').textContent='$'+currentProduct.price;
document.getElementById('modalDesc').textContent=currentProduct.desc;
document.getElementById('modalTag').textContent=COLLECTIONS[currentProduct.col].name+' COLLECTION';
document.getElementById('modalTag').style.color=accent;
document.getElementById('modalSizes').innerHTML=currentProduct.sizes.map(s=>'<button class="size-btn" style="--accent:'+accent+'" onclick="selectSize(this,\''+s+'\')">'+s+'</button>').join('');
document.querySelector('.btn-primary').style.background=accent;
document.getElementById('modal').classList.add('open');}window.openModal=openModal;
function closeModal(){document.getElementById('modal').classList.remove('open');currentProduct=null;}window.closeModal=closeModal;
function selectSize(el,s){selectedSize=s;document.querySelectorAll('.size-btn').forEach(b=>b.classList.remove('sel'));el.classList.add('sel');}window.selectSize=selectSize;
function addFromModal(){if(!currentProduct)return;addToCart(currentProduct);closeModal();}window.addFromModal=addFromModal;
function addToCart(p){const ex=cart.find(c=>c.id===p.id);if(ex)ex.qty++;else cart.push({...p,qty:1,size:selectedSize||p.sizes[1]});updateCartUI();}
function removeFromCart(id){const i=cart.findIndex(c=>c.id===id);if(i>-1)cart.splice(i,1);updateCartUI();}window.removeFromCart=removeFromCart;
function updateCartUI(){const cnt=document.getElementById('cartCount');const tot=cart.reduce((s,c)=>s+c.qty,0);cnt.textContent=tot;cnt.classList.toggle('show',tot>0);
const el=document.getElementById('cartItems');if(!cart.length){el.innerHTML='<div class="cart-empty">Your collection awaits</div>';}
else{el.innerHTML=cart.map(c=>{const accent=COLLECTIONS[c.col].accent;return '<div class="cart-item"><div class="cart-thumb" style="border-color:'+accent+'30"><span style="color:'+accent+'">'+COLLECTIONS[c.col].name.charAt(0)+'</span></div><div class="cart-info"><div class="cart-name">'+c.name+(c.qty>1?' \u00d7 '+c.qty:'')+'</div><div class="cart-price" style="color:'+accent+'">$'+(c.price*c.qty)+'</div></div><button class="cart-remove" onclick="removeFromCart(\''+c.id+'\')">\u2715</button></div>';}).join('');}
document.getElementById('cartTotal').textContent='$'+cart.reduce((s,c)=>s+c.price*c.qty,0);}
function toggleCart(){document.getElementById('cart').classList.toggle('open');}window.toggleCart=toggleCart;
function checkout(){if(!cart.length)return;
if(typeof wp!=='undefined'||document.querySelector('body.woocommerce')){const items=cart.map(c=>({id:c.sku,quantity:c.qty}));
Promise.all(items.map(it=>fetch('/wp-json/wc/store/v1/cart/items',{method:'POST',headers:{'Content-Type':'application/json','Nonce':window.wcStoreApiNonce||''},body:JSON.stringify({id:it.id,quantity:it.quantity})}))).then(()=>window.location.href='/checkout').catch(()=>window.location.href='/checkout');
}else{alert('SKYYROSE PRE-ORDER:\n'+cart.map(c=>'['+COLLECTIONS[c.col].name+'] '+c.name+' \u00d7 '+c.qty+' = $'+(c.price*c.qty)).join('\n')+'\n\nTotal: $'+cart.reduce((s,c)=>s+c.price*c.qty,0));}}window.checkout=checkout;

/* ── EXCLUSIVE SIGN-IN ── */
function toggleSignIn(){document.getElementById('signInPanel').classList.toggle('open');}window.toggleSignIn=toggleSignIn;
function handleSignIn(e){e.preventDefault();const email=document.getElementById('signEmail').value;const code=document.getElementById('signCode').value;
if(!email){alert('Please enter your email');return;}
if(typeof wp!=='undefined'){fetch('/wp-json/skyyrose/v1/exclusive-access',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,code})}).then(r=>r.json()).then(d=>{if(d.success){document.getElementById('signInPanel').classList.remove('open');document.getElementById('exclusiveBanner').classList.add('authenticated');document.getElementById('authStatus').textContent='Welcome, '+email.split('@')[0];}else{alert(d.message||'Invalid access code');}}).catch(()=>mockSignIn(email,code));}
else{mockSignIn(email,code);}}window.handleSignIn=handleSignIn;
function mockSignIn(email,code){if(code==='SKYYROSE2025'||code===''){document.getElementById('signInPanel').classList.remove('open');document.getElementById('exclusiveBanner').classList.add('authenticated');document.getElementById('authStatus').textContent='Welcome, '+email.split('@')[0];document.querySelectorAll('.exclusive-tag').forEach(t=>t.style.display='inline');}else{alert('Invalid access code. Try SKYYROSE2025 for demo.');}}

function initGrain(){const c=document.getElementById('grain'),ctx=c.getContext('2d');c.width=256;c.height=256;
(function draw(){const img=ctx.createImageData(256,256);for(let i=0;i<img.data.length;i+=4){const v=Math.random()*255;img.data[i]=img.data[i+1]=img.data[i+2]=v;img.data[i+3]=255;}ctx.putImageData(img,0,0);requestAnimationFrame(draw);})();}

function simulateLoading(){let p=0;const f=document.getElementById('loadFill');
const iv=setInterval(()=>{p+=Math.random()*10+3;if(p>=100){p=100;clearInterval(iv);
setTimeout(()=>{document.getElementById('loader').classList.add('done');
['nav','mainUI','exclusiveBanner'].forEach(id=>{const el=document.getElementById(id);if(el)el.classList.add('show');});
renderProducts();initGrain();},600);}f.style.width=p+'%';},180);}

function onResize(){camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);composer.setSize(innerWidth,innerHeight);}

function loop(){const t=clock.getElapsedTime();
if(particles){particles.rotation.y=t*.005;const pos=particles.geometry.attributes.position;
for(let i=0;i<pos.count;i++){pos.array[i*3+1]+=Math.sin(t*.2+i*.05)*.0004;if(pos.array[i*3+1]>15)pos.array[i*3+1]=0;}pos.needsUpdate=true;}
scene.traverse(o=>{if(o.userData.float){o.position.y=o.userData.float.baseY+Math.sin(t*o.userData.float.speed+o.userData.float.offset)*.25;o.rotation.y+=o.userData.float.rotSpeed*.002;o.rotation.x=Math.sin(t*.4)*.04;}
if(o.userData.ringSpeed){o.rotation.z+=o.userData.ringSpeed*.01;o.rotation.x+=o.userData.ringSpeed*.005;}
if(o.userData.core){o.rotation.y=t*.15;o.children.forEach((c,i)=>{if(i===0)c.position.y=2+Math.sin(t*.3)*.05;});}});
controls.update();composer.render();}
init();

