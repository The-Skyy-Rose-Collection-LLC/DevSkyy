
import*as THREE from'three';
import{OrbitControls}from'three/addons/controls/OrbitControls.js';
import{EffectComposer}from'three/addons/postprocessing/EffectComposer.js';
import{RenderPass}from'three/addons/postprocessing/RenderPass.js';
import{UnrealBloomPass}from'three/addons/postprocessing/UnrealBloomPass.js';
import{ShaderPass}from'three/addons/postprocessing/ShaderPass.js';
import{OutputPass}from'three/addons/postprocessing/OutputPass.js';

const PRODUCTS=[
{id:'lh-001',name:'Heartbreak Hoodie',price:195,sku:'SR-LH-HB-H',sizes:['S','M','L','XL','XXL'],desc:'Premium French terry with hand-distressed heart patch on chest. Barbed wire embroidery cascades along sleeves. Oversized fit, dropped shoulder, kangaroo pocket.',pos:new THREE.Vector3(-3.5,2.5,4)},
{id:'lh-002',name:'Tears Jacket',price:325,sku:'SR-LH-TEARS-J',sizes:['S','M','L','XL'],desc:'Full-grain leather biker jacket with thorn-wrapped heart hardware. Burgundy satin interior with hidden rose pocket. Asymmetric zip, silver hardware.',pos:new THREE.Vector3(4,2.2,3)},
{id:'lh-003',name:'Wounded Tee',price:85,sku:'SR-LH-WOUND-T',sizes:['S','M','L','XL','XXL'],desc:'Oversized boxy tee with cracked heart screenprint in crimson ink. Vintage acid wash effect, raw hem, reinforced neckline.',pos:new THREE.Vector3(-3,1.8,-2.5)},
{id:'lh-004',name:'Scar Pants',price:165,sku:'SR-LH-SCAR-P',sizes:['28','30','32','34','36'],desc:'Tailored wide-leg trouser with decorative scar stitching along seams. Burgundy racing stripe, relaxed drape, premium twill.',pos:new THREE.Vector3(3.5,1.6,-3)}
];
const VIEWS=[
{p:new THREE.Vector3(0,4,13),t:new THREE.Vector3(0,2,0)},
{p:new THREE.Vector3(-6,3,2),t:new THREE.Vector3(0,3,0)},
{p:new THREE.Vector3(0,8,.1),t:new THREE.Vector3(0,5,0)},
{p:new THREE.Vector3(5,6,-5),t:new THREE.Vector3(0,2,0)}
];

let scene,camera,renderer,composer,controls,clock,particles;
let currentView=0,animating=false;
const cart=[];const hotspotEls=[];let currentProduct=null;let selectedSize=null;

function init(){
clock=new THREE.Clock();scene=new THREE.Scene();
scene.fog=new THREE.FogExp2(0x080210,.013);scene.background=new THREE.Color(0x050208);
camera=new THREE.PerspectiveCamera(50,innerWidth/innerHeight,.1,100);camera.position.copy(VIEWS[0].p);
renderer=new THREE.WebGLRenderer({canvas:document.getElementById('scene'),antialias:true,powerPreference:'high-performance'});
renderer.setSize(innerWidth,innerHeight);renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=.9;
renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.04;
controls.enablePan=false;controls.maxPolarAngle=Math.PI*.55;controls.minDistance=3;controls.maxDistance=20;
controls.autoRotate=true;controls.autoRotateSpeed=.1;controls.target.copy(VIEWS[0].t);
buildScene();buildPost();buildHotspots();initGrain();
window.addEventListener('resize',onResize);renderer.setAnimationLoop(loop);simulateLoading();
}

function buildScene(){
const darkMat=new THREE.MeshStandardMaterial({color:0x1a0818,metalness:.6,roughness:.3});
const roseMat=new THREE.MeshStandardMaterial({color:0xE91E63,emissive:0x880E4F,emissiveIntensity:.3,metalness:.9,roughness:.1});
const rgMat=new THREE.MeshStandardMaterial({color:0xB76E79,metalness:.9,roughness:.1});

// Checker floor
const floorGeo=new THREE.PlaneGeometry(40,40,40,40);
const fp=floorGeo.attributes.position;const fc=new Float32Array(fp.count*3);
for(let i=0;i<fp.count;i++){
const x=Math.floor((fp.getX(i)+20)/2),z=Math.floor((fp.getY(i)+20)/2);
const dark=(x+z)%2===0;const c=dark?new THREE.Color(0x0a0510):new THREE.Color(0x15081a);
fc[i*3]=c.r;fc[i*3+1]=c.g;fc[i*3+2]=c.b;}
floorGeo.setAttribute('color',new THREE.BufferAttribute(fc,3));
const floor=new THREE.Mesh(floorGeo,new THREE.MeshStandardMaterial({vertexColors:true,metalness:.85,roughness:.2}));
floor.rotation.x=-Math.PI/2;floor.receiveShadow=true;scene.add(floor);

// Gothic arches - 6 around perimeter
for(let i=0;i<6;i++){
const a=(i/6)*Math.PI*2,r=9;const g=new THREE.Group();
g.position.set(Math.cos(a)*r,0,Math.sin(a)*r);g.lookAt(0,0,0);
const pilL=new THREE.Mesh(new THREE.CylinderGeometry(.15,.18,7,8),darkMat);pilL.position.set(-.8,3.5,0);g.add(pilL);
const pilR=pilL.clone();pilR.position.set(.8,3.5,0);g.add(pilR);
const archCurve=new THREE.CatmullRomCurve3([new THREE.Vector3(-.8,7,0),new THREE.Vector3(-.4,8.2,0),new THREE.Vector3(0,8.5,0),new THREE.Vector3(.4,8.2,0),new THREE.Vector3(.8,7,0)]);
g.add(new THREE.Mesh(new THREE.TubeGeometry(archCurve,16,.1,8,false),darkMat));
// Rose window
const rw=new THREE.Mesh(new THREE.RingGeometry(.3,.6,6),new THREE.MeshBasicMaterial({color:0xE91E63,transparent:true,opacity:.15,side:THREE.DoubleSide}));
rw.position.set(0,7.2,.1);g.add(rw);scene.add(g);}

// Throne
const throneG=new THREE.Group();throneG.position.set(0,0,-6);
throneG.add(Object.assign(new THREE.Mesh(new THREE.BoxGeometry(1.8,.3,1.5),new THREE.MeshStandardMaterial({color:0x2a0818,metalness:.5,roughness:.4})),{position:new THREE.Vector3(0,1,0)}));
throneG.add(Object.assign(new THREE.Mesh(new THREE.BoxGeometry(1.8,3,.15),new THREE.MeshStandardMaterial({color:0x1a0510,metalness:.6,roughness:.3})),{position:new THREE.Vector3(0,2.5,-.7)}));
const crown=new THREE.Mesh(new THREE.ConeGeometry(.4,.6,5),roseMat);crown.position.set(0,4.2,-.7);throneG.add(crown);
const armL=new THREE.Mesh(new THREE.BoxGeometry(.15,1,.6),new THREE.MeshStandardMaterial({color:0x1a0510,metalness:.6}));
armL.position.set(-.9,1.5,-.3);throneG.add(armL);throneG.add(Object.assign(armL.clone(),{position:new THREE.Vector3(.9,1.5,-.3)}));
scene.add(throneG);

// Chandelier
const chanG=new THREE.Group();chanG.position.set(0,7.5,0);chanG.userData.chan=true;
for(let tier=0;tier<3;tier++){const cr=.8+tier*.5,cn=4+tier*2;
const ring=new THREE.Mesh(new THREE.TorusGeometry(cr,.03,8,24),rgMat);
ring.rotation.x=Math.PI/2;ring.position.y=-tier*.6;chanG.add(ring);
for(let i=0;i<cn;i++){const ca=(i/cn)*Math.PI*2;
const candle=new THREE.Mesh(new THREE.CylinderGeometry(.02,.025,.15,6),new THREE.MeshStandardMaterial({color:0xF8BBD9,emissive:0xE91E63,emissiveIntensity:.3}));
candle.position.set(Math.cos(ca)*cr,-tier*.6-.1,Math.sin(ca)*cr);chanG.add(candle);
const flame=new THREE.PointLight(0xE91E63,.25,4);flame.position.copy(candle.position);flame.position.y+=.1;chanG.add(flame);}}
for(let i=0;i<4;i++){const a=(i/4)*Math.PI*2,cr2=.4;
chanG.add(Object.assign(new THREE.Mesh(new THREE.CylinderGeometry(.008,.008,3,4),rgMat),{position:new THREE.Vector3(Math.cos(a)*cr2,1.5,Math.sin(a)*cr2)}));}
scene.add(chanG);

// Floating hearts
for(let i=0;i<18;i++){
const hs=new THREE.Shape();const hx=0,hy=0;
hs.moveTo(hx+.25,hy+.25);hs.bezierCurveTo(hx+.25,hy+.25,hx+.2,hy,hx,hy);
hs.bezierCurveTo(hx-.3,hy,hx-.3,hy+.35,hx-.3,hy+.35);hs.bezierCurveTo(hx-.3,hy+.55,hx-.1,hy+.77,hx+.25,hy+.95);
hs.bezierCurveTo(hx+.6,hy+.77,hx+.8,hy+.55,hx+.8,hy+.35);hs.bezierCurveTo(hx+.8,hy+.35,hx+.8,hy,hx+.5,hy);
hs.bezierCurveTo(hx+.35,hy,hx+.25,hy+.25,hx+.25,hy+.25);
const geo=new THREE.ExtrudeGeometry(hs,{depth:.1,bevelEnabled:true,bevelThickness:.02,bevelSize:.02,bevelSegments:2});
const mat=new THREE.MeshStandardMaterial({color:new THREE.Color().lerpColors(new THREE.Color(0xE91E63),new THREE.Color(0x880E4F),Math.random()),metalness:.5,roughness:.4,transparent:true,opacity:.6+Math.random()*.4});
const heart=new THREE.Mesh(geo,mat);const ha=Math.random()*Math.PI*2,hr=3+Math.random()*5;
heart.position.set(Math.cos(ha)*hr,2+Math.random()*5,Math.sin(ha)*hr);
const s=.12+Math.random()*.18;heart.scale.set(s,s,s);
heart.rotation.set(Math.random()*Math.PI,Math.random()*Math.PI,Math.random()*Math.PI);
heart.userData.float={speed:.3+Math.random()*.4,offset:Math.random()*Math.PI*2,baseY:heart.position.y};
scene.add(heart);}

// Particles - rose petals
const pCnt=5000;const pGe=new THREE.BufferGeometry();
const pP=new Float32Array(pCnt*3),pC=new Float32Array(pCnt*3);
for(let i=0;i<pCnt;i++){pP[i*3]=(Math.random()-.5)*25;pP[i*3+1]=Math.random()*12;pP[i*3+2]=(Math.random()-.5)*25;
const c=Math.random()>.6?new THREE.Color(0xE91E63):new THREE.Color(0xF8BBD9);pC[i*3]=c.r;pC[i*3+1]=c.g;pC[i*3+2]=c.b;}
pGe.setAttribute('position',new THREE.BufferAttribute(pP,3));pGe.setAttribute('color',new THREE.BufferAttribute(pC,3));
particles=new THREE.Points(pGe,new THREE.PointsMaterial({size:.05,vertexColors:true,transparent:true,opacity:.45,blending:THREE.AdditiveBlending,depthWrite:false}));
scene.add(particles);

// Lighting
scene.add(new THREE.AmbientLight(0x1a0818,.3));
const warmUp=new THREE.PointLight(0xE91E63,2,18);warmUp.position.set(0,1,0);warmUp.castShadow=true;warmUp.shadow.mapSize.set(1024,1024);scene.add(warmUp);
scene.add(Object.assign(new THREE.DirectionalLight(0x4a2040,.25),{position:new THREE.Vector3(-4,10,4)}));
scene.add(Object.assign(new THREE.PointLight(0x880E4F,1.2,10),{position:new THREE.Vector3(-5,4,-3)}));
scene.add(Object.assign(new THREE.PointLight(0xF8BBD9,.8,10),{position:new THREE.Vector3(5,5,3)}));
const sp=new THREE.SpotLight(0xE91E63,.6,12,Math.PI/6,.5);sp.position.set(0,9,0);sp.target.position.set(0,0,-6);scene.add(sp);scene.add(sp.target);
}

function buildPost(){
const rt=new THREE.WebGLRenderTarget(innerWidth,innerHeight,{type:THREE.HalfFloatType});
composer=new EffectComposer(renderer,rt);composer.addPass(new RenderPass(scene,camera));
composer.addPass(new UnrealBloomPass(new THREE.Vector2(innerWidth,innerHeight),1.5,.5,.8));
composer.addPass(new ShaderPass({uniforms:{tDiffuse:{value:null},amount:{value:.001}},
vertexShader:'varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',
fragmentShader:'uniform sampler2D tDiffuse;uniform float amount;varying vec2 vUv;void main(){vec2 d=amount*(vUv-.5);gl_FragColor=vec4(texture2D(tDiffuse,vUv+d).r,texture2D(tDiffuse,vUv).g,texture2D(tDiffuse,vUv-d).b,1.);}'}));
composer.addPass(new ShaderPass({uniforms:{tDiffuse:{value:null},darkness:{value:1.1},offset:{value:1.0}},
vertexShader:'varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',
fragmentShader:'uniform sampler2D tDiffuse;uniform float darkness;uniform float offset;varying vec2 vUv;void main(){vec4 c=texture2D(tDiffuse,vUv);vec2 u=(vUv-.5)*2.;gl_FragColor=vec4(c.rgb*clamp(1.-dot(u,u)*darkness+offset,0.,1.),c.a);}'}));
composer.addPass(new OutputPass());}

function buildHotspots(){const c=document.getElementById('hotspots');
PRODUCTS.forEach((p,i)=>{const e=document.createElement('div');e.className='hotspot';
e.innerHTML='<div class="hs-ring"><div class="hs-core"></div></div><div class="hs-label">'+p.name+'<span>$'+p.price+'</span></div>';
e.addEventListener('click',()=>openModal(i));c.appendChild(e);hotspotEls.push(e);});}

function updateHotspots(){PRODUCTS.forEach((p,i)=>{const e=hotspotEls[i];const v=p.pos.clone().project(camera);
const x=(v.x*.5+.5)*innerWidth,y=(-(v.y*.5)+.5)*innerHeight;
if(v.z<1&&x>-50&&x<innerWidth+50&&y>-50&&y<innerHeight+50){e.style.display='block';e.style.left=(x-26)+'px';e.style.top=(y-26)+'px';}
else{e.style.display='none';}});}

function openModal(i){currentProduct=PRODUCTS[i];selectedSize=null;
document.getElementById('modalName').textContent=currentProduct.name;
document.getElementById('modalPrice').textContent='$'+currentProduct.price;
document.getElementById('modalDesc').textContent=currentProduct.desc;
document.getElementById('modalSizes').innerHTML=currentProduct.sizes.map(s=>'<button class="size-btn" onclick="selectSize(this,\''+s+'\')">'+s+'</button>').join('');
document.getElementById('modal').classList.add('open');}
window.openModal=openModal;
function closeModal(){document.getElementById('modal').classList.remove('open');currentProduct=null;}window.closeModal=closeModal;
function selectSize(el,s){selectedSize=s;document.querySelectorAll('.size-btn').forEach(b=>b.classList.remove('sel'));el.classList.add('sel');}window.selectSize=selectSize;
function addFromModal(){if(!currentProduct)return;addToCart(currentProduct);closeModal();}window.addFromModal=addFromModal;
function addToCart(p){const ex=cart.find(c=>c.id===p.id);if(ex)ex.qty++;else cart.push({...p,qty:1,size:selectedSize||p.sizes[1]});updateCartUI();}
function removeFromCart(id){const i=cart.findIndex(c=>c.id===id);if(i>-1)cart.splice(i,1);updateCartUI();}window.removeFromCart=removeFromCart;
function updateCartUI(){const cnt=document.getElementById('cartCount');const tot=cart.reduce((s,c)=>s+c.qty,0);cnt.textContent=tot;cnt.classList.toggle('show',tot>0);
const el=document.getElementById('cartItems');if(!cart.length){el.innerHTML='<div class="cart-empty">Love has not yet found its vessel</div>';}
else{el.innerHTML=cart.map(c=>'<div class="cart-item"><div class="cart-thumb"></div><div class="cart-info"><div class="cart-name">'+c.name+(c.qty>1?' × '+c.qty:'')+'</div><div class="cart-price">$'+(c.price*c.qty)+'</div></div><button class="cart-remove" onclick="removeFromCart(\''+c.id+'\')">✕</button></div>').join('');}
document.getElementById('cartTotal').textContent='$'+cart.reduce((s,c)=>s+c.price*c.qty,0);}
function toggleCart(){document.getElementById('cart').classList.toggle('open');}window.toggleCart=toggleCart;
function checkout(){if(!cart.length)return;
if(typeof wp!=='undefined'||document.querySelector('body.woocommerce')){const items=cart.map(c=>({id:c.sku,quantity:c.qty}));
Promise.all(items.map(it=>fetch('/wp-json/wc/store/v1/cart/items',{method:'POST',headers:{'Content-Type':'application/json','Nonce':window.wcStoreApiNonce||''},body:JSON.stringify({id:it.id,quantity:it.quantity})}))).then(()=>window.location.href='/checkout').catch(()=>window.location.href='/checkout');
}else{alert('LOVE HURTS Order:\n'+cart.map(c=>c.name+' × '+c.qty+' = $'+(c.price*c.qty)).join('\n')+'\n\nTotal: $'+cart.reduce((s,c)=>s+c.price*c.qty,0));}}
window.checkout=checkout;
function launchAR(){alert('AR Experience launching...\nRequires mobile device with ARCore/ARKit.');}window.launchAR=launchAR;

function showView(idx){if(animating||idx===currentView)return;animating=true;currentView=idx;
document.querySelectorAll('.room-btn').forEach((b,i)=>b.classList.toggle('active',i===idx));
const tgt=VIEWS[idx],sp=camera.position.clone(),st=controls.target.clone(),dur=2400,start=performance.now();
function av(now){const el=now-start,t=Math.min(el/dur,1);const e=t<.5?4*t*t*t:(t-1)*(2*t-2)*(2*t-2)+1;
camera.position.lerpVectors(sp,tgt.p,e);controls.target.lerpVectors(st,tgt.t,e);controls.update();
if(t<1)requestAnimationFrame(av);else animating=false;}requestAnimationFrame(av);}
window.showView=showView;

function initGrain(){const c=document.getElementById('grain'),ctx=c.getContext('2d');c.width=256;c.height=256;
(function draw(){const img=ctx.createImageData(256,256);for(let i=0;i<img.data.length;i+=4){const v=Math.random()*255;img.data[i]=img.data[i+1]=img.data[i+2]=v;img.data[i+3]=255;}ctx.putImageData(img,0,0);requestAnimationFrame(draw);})();}

function simulateLoading(){let p=0;const f=document.getElementById('loadFill');
const iv=setInterval(()=>{p+=Math.random()*12+4;if(p>=100){p=100;clearInterval(iv);
setTimeout(()=>{document.getElementById('loader').classList.add('done');
['nav','rooms','info','cta'].forEach(id=>document.getElementById(id).classList.add('show'));},500);}
f.style.width=p+'%';},180);}

function onResize(){camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);composer.setSize(innerWidth,innerHeight);}

function loop(){const t=clock.getElapsedTime();
if(particles){particles.rotation.y=t*.008;const pos=particles.geometry.attributes.position;
for(let i=0;i<pos.count;i++){pos.array[i*3+1]-=.002;if(pos.array[i*3+1]<0)pos.array[i*3+1]=12;}pos.needsUpdate=true;}
scene.traverse(o=>{if(o.userData.chan){o.rotation.y=t*.05;}
if(o.userData.float){o.position.y=o.userData.float.baseY+Math.sin(t*o.userData.float.speed+o.userData.float.offset)*.3;
o.rotation.y+=.002;o.rotation.z=Math.sin(t*.5+o.userData.float.offset)*.05;}});
controls.update();updateHotspots();composer.render();}
init();

