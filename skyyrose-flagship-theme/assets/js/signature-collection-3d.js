import*as THREE from'three';
import{OrbitControls}from'three/addons/controls/OrbitControls.js';
import{EffectComposer}from'three/addons/postprocessing/EffectComposer.js';
import{RenderPass}from'three/addons/postprocessing/RenderPass.js';
import{UnrealBloomPass}from'three/addons/postprocessing/UnrealBloomPass.js';
import{ShaderPass}from'three/addons/postprocessing/ShaderPass.js';
import{OutputPass}from'three/addons/postprocessing/OutputPass.js';
const PRODUCTS=[
{id:'sg-001',name:'Foundation Blazer',price:395,sku:'SR-SG-BLAZ',sizes:['S','M','L','XL'],desc:'Italian wool-blend blazer with rose-gold hardware. Signature lining with Oakland-inspired motif.',pos:new THREE.Vector3(-1.5,2.5,2)},
{id:'sg-002',name:'Essential Trouser',price:245,sku:'SR-SG-TROU',sizes:['28','30','32','34','36'],desc:'Tailored wide-leg trouser in premium wool. Gold-foil branding on interior waistband.',pos:new THREE.Vector3(1.5,2.2,1.5)},
{id:'sg-003',name:'Luxury Tee',price:125,sku:'SR-SG-TEE',sizes:['S','M','L','XL','XXL'],desc:'400gsm Supima cotton with metallic rose-gold embroidered crest. Relaxed fit, raw hem.',pos:new THREE.Vector3(-2,1.8,-1)},
{id:'sg-004',name:'Heritage Coat',price:595,sku:'SR-SG-COAT',sizes:['S','M','L','XL'],desc:'Double-breasted cashmere-blend overcoat. Rose-gold closure hardware, satin interior.',pos:new THREE.Vector3(2,2.4,-1.5)},
{id:'sg-005',name:'Classic Oxford',price:175,sku:'SR-SG-OXFD',sizes:['S','M','L','XL','XXL'],desc:'Premium poplin with signature rose-gold collar stays. Mother-of-pearl buttons.',pos:new THREE.Vector3(0,1.6,-3)}];
const VIEWS=[{p:new THREE.Vector3(0,3,10),t:new THREE.Vector3(0,1.5,0)},{p:new THREE.Vector3(-5,2,5),t:new THREE.Vector3(0,1.5,0)},{p:new THREE.Vector3(0,2.5,-6),t:new THREE.Vector3(0,2,0)},{p:new THREE.Vector3(0,14,.1),t:new THREE.Vector3(0,0,0)}];
let scene,camera,renderer,composer,controls,clock,particles;let currentView=0,animating=false;const cart=[];const hotspotEls=[];let currentProduct=null;let selectedSize=null;
function init(){clock=new THREE.Clock();scene=new THREE.Scene();scene.fog=new THREE.FogExp2(0x040406,.01);scene.background=new THREE.Color(0x030304);
camera=new THREE.PerspectiveCamera(48,innerWidth/innerHeight,.1,100);camera.position.copy(VIEWS[0].p);
renderer=new THREE.WebGLRenderer({canvas:document.getElementById('scene'),antialias:true,powerPreference:'high-performance'});
renderer.setSize(innerWidth,innerHeight);renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=.95;renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.04;controls.enablePan=false;controls.maxPolarAngle=Math.PI*.52;controls.minDistance=3;controls.maxDistance=18;controls.autoRotate=true;controls.autoRotateSpeed=.08;controls.target.copy(VIEWS[0].t);
buildScene();buildPost();buildHotspots();initGrain();window.addEventListener('resize',onResize);renderer.setAnimationLoop(loop);simulateLoading();}
function buildScene(){const mm=new THREE.MeshStandardMaterial({color:0x1a1a1e,metalness:.7,roughness:.25});const gm=new THREE.MeshStandardMaterial({color:0xD4AF37,metalness:.95,roughness:.05});const fm=new THREE.MeshStandardMaterial({color:0x0a0a0c,metalness:.92,roughness:.12});
scene.add(Object.assign(new THREE.Mesh(new THREE.PlaneGeometry(40,40),fm),{rotation:{x:-Math.PI/2},receiveShadow:true}));
const rw=new THREE.Mesh(new THREE.BoxGeometry(3,.02,16),new THREE.MeshStandardMaterial({color:0x0f0f12,metalness:.95,roughness:.08}));rw.position.y=.01;scene.add(rw);
const em=new THREE.MeshBasicMaterial({color:0xD4AF37});[-1.5,1.5].forEach(x=>{scene.add(Object.assign(new THREE.Mesh(new THREE.BoxGeometry(.02,.01,16),em),{position:new THREE.Vector3(x,.02,0)}));});
for(let i=0;i<7;i++){const z=-6+i*2;const mg=new THREE.Group();mg.position.set(0,.01,z);
mg.add(Object.assign(new THREE.Mesh(new THREE.CylinderGeometry(.18,.15,1.2,8),mm),{position:new THREE.Vector3(0,1.8,0)}));
mg.add(Object.assign(new THREE.Mesh(new THREE.IcosahedronGeometry(.15,1),mm),{position:new THREE.Vector3(0,2.55,0)}));
mg.add(Object.assign(new THREE.Mesh(new THREE.CylinderGeometry(.15,.12,.4,8),mm),{position:new THREE.Vector3(0,1.1,0)}));
[-0.08,0.08].forEach(x=>{mg.add(Object.assign(new THREE.Mesh(new THREE.CylinderGeometry(.06,.05,1,6),mm),{position:new THREE.Vector3(x,.45,0)}));});
mg.add(new THREE.Mesh(new THREE.CylinderGeometry(.3,.35,.08,16),gm));mg.userData.mannequin={baseY:.01,speed:.3+Math.random()*.2,offset:Math.random()*Math.PI*2};scene.add(mg);}
for(let s=-1;s<=1;s+=2){for(let i=0;i<11;i++){const z=-5+i;const cg=new THREE.Group();cg.position.set(s*3.5,0,z);
cg.add(Object.assign(new THREE.Mesh(new THREE.BoxGeometry(.35,.02,.35),mm),{position:new THREE.Vector3(0,.45,0)}));
for(let l=0;l<4;l++){cg.add(Object.assign(new THREE.Mesh(new THREE.CylinderGeometry(.01,.01,.45,4),gm),{position:new THREE.Vector3((l%2-.5)*.28,.225,(Math.floor(l/2)-.5)*.28)}));}
cg.add(Object.assign(new THREE.Mesh(new THREE.BoxGeometry(.35,.3,.02),mm),{position:new THREE.Vector3(0,.6,-.17)}));scene.add(cg);}}
for(let i=0;i<7;i++){const z=-6+i*2;const sg=new THREE.Group();sg.add(Object.assign(new THREE.Mesh(new THREE.CylinderGeometry(.02,.02,5,6),mm),{position:new THREE.Vector3(0,2.5,0)}));
const hm=i%2===0?gm:new THREE.MeshStandardMaterial({color:0xE5E4E2,metalness:.9,roughness:.1});
sg.add(Object.assign(new THREE.Mesh(new THREE.CylinderGeometry(.1,.15,.2,8),hm),{position:new THREE.Vector3(0,5,0)}));
sg.position.set(i%2===0?-2:2,0,z);scene.add(sg);
const sl=new THREE.SpotLight(i%2===0?0xD4AF37:0xE5E4E2,.5,8,Math.PI/5,.6);sl.position.set(i%2===0?-2:2,5,z);sl.target.position.set(0,0,z);sl.castShadow=true;sl.shadow.mapSize.set(512,512);scene.add(sl);scene.add(sl.target);}
for(let i=0;i<8;i++){const a=Math.random()*Math.PI*2,r=4+Math.random()*4;const d=new THREE.Mesh(new THREE.OctahedronGeometry(.3+Math.random()*.2,0),new THREE.MeshBasicMaterial({color:0xD4AF37,wireframe:true,transparent:true,opacity:.2}));
d.position.set(Math.cos(a)*r,3+Math.random()*4,Math.sin(a)*r);d.userData.float={speed:.2+Math.random()*.3,offset:Math.random()*Math.PI*2,baseY:d.position.y,rotSpeed:.5+Math.random()*.5};scene.add(d);}
for(let i=0;i<5;i++){const t=new THREE.Mesh(new THREE.TorusGeometry(1.5+i*.4,.01,8,48),new THREE.MeshStandardMaterial({color:0xB76E79,metalness:.95,roughness:.05,transparent:true,opacity:.15}));
t.position.set(0,6+i*.5,0);t.rotation.x=Math.PI/2+Math.random()*.2;t.userData.ringSpeed=.08+i*.02;scene.add(t);}
const pCnt=4000;const pGe=new THREE.BufferGeometry();const pP=new Float32Array(pCnt*3),pC=new Float32Array(pCnt*3);
for(let i=0;i<pCnt;i++){pP[i*3]=(Math.random()-.5)*25;pP[i*3+1]=Math.random()*12;pP[i*3+2]=(Math.random()-.5)*25;const c=Math.random()>.5?new THREE.Color(0xD4AF37):new THREE.Color(0xB76E79);pC[i*3]=c.r;pC[i*3+1]=c.g;pC[i*3+2]=c.b;}
pGe.setAttribute('position',new THREE.BufferAttribute(pP,3));pGe.setAttribute('color',new THREE.BufferAttribute(pC,3));
particles=new THREE.Points(pGe,new THREE.PointsMaterial({size:.04,vertexColors:true,transparent:true,opacity:.4,blending:THREE.AdditiveBlending,depthWrite:false}));scene.add(particles);
scene.add(new THREE.AmbientLight(0x0a0a10,.3));const kl=new THREE.DirectionalLight(0xD4AF37,.4);kl.position.set(-3,8,5);kl.castShadow=true;kl.shadow.mapSize.set(1024,1024);scene.add(kl);
scene.add(Object.assign(new THREE.PointLight(0xD4AF37,1.5,15),{position:new THREE.Vector3(0,1,0)}));scene.add(Object.assign(new THREE.PointLight(0xB76E79,1,12),{position:new THREE.Vector3(-5,4,-2)}));scene.add(Object.assign(new THREE.PointLight(0xE5E4E2,.6,12),{position:new THREE.Vector3(5,5,2)}));}
function buildPost(){const rt=new THREE.WebGLRenderTarget(innerWidth,innerHeight,{type:THREE.HalfFloatType});composer=new EffectComposer(renderer,rt);composer.addPass(new RenderPass(scene,camera));
composer.addPass(new UnrealBloomPass(new THREE.Vector2(innerWidth,innerHeight),1.0,.4,.85));
composer.addPass(new ShaderPass({uniforms:{tDiffuse:{value:null},amount:{value:.0008}},vertexShader:'varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',fragmentShader:'uniform sampler2D tDiffuse;uniform float amount;varying vec2 vUv;void main(){vec2 d=amount*(vUv-.5);gl_FragColor=vec4(texture2D(tDiffuse,vUv+d).r,texture2D(tDiffuse,vUv).g,texture2D(tDiffuse,vUv-d).b,1.);}'}));
composer.addPass(new ShaderPass({uniforms:{tDiffuse:{value:null},darkness:{value:.9},offset:{value:1.0}},vertexShader:'varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',fragmentShader:'uniform sampler2D tDiffuse;uniform float darkness;uniform float offset;varying vec2 vUv;void main(){vec4 c=texture2D(tDiffuse,vUv);vec2 u=(vUv-.5)*2.;gl_FragColor=vec4(c.rgb*clamp(1.-dot(u,u)*darkness+offset,0.,1.),c.a);}'}));
composer.addPass(new OutputPass());}
function buildHotspots(){const c=document.getElementById('hotspots');PRODUCTS.forEach((p,i)=>{const e=document.createElement('div');e.className='hotspot';e.innerHTML='<div class="hs-ring"><div class="hs-core"></div></div><div class="hs-label">'+p.name+'<span>$'+p.price+'</span></div>';e.addEventListener('click',()=>openModal(i));c.appendChild(e);hotspotEls.push(e);});}
function updateHotspots(){PRODUCTS.forEach((p,i)=>{const e=hotspotEls[i];const v=p.pos.clone().project(camera);const x=(v.x*.5+.5)*innerWidth,y=(-(v.y*.5)+.5)*innerHeight;if(v.z<1&&x>-50&&x<innerWidth+50&&y>-50&&y<innerHeight+50){e.style.display='block';e.style.left=(x-26)+'px';e.style.top=(y-26)+'px';}else{e.style.display='none';}});}
function openModal(i){currentProduct=PRODUCTS[i];selectedSize=null;document.getElementById('modalName').textContent=currentProduct.name;document.getElementById('modalPrice').textContent='$'+currentProduct.price;document.getElementById('modalDesc').textContent=currentProduct.desc;document.getElementById('modalSizes').innerHTML=currentProduct.sizes.map(s=>'<button class="size-btn" onclick="selectSize(this,\''+s+'\')">'+s+'</button>').join('');document.getElementById('modal').classList.add('open');}window.openModal=openModal;
function closeModal(){document.getElementById('modal').classList.remove('open');currentProduct=null;}window.closeModal=closeModal;
function selectSize(el,s){selectedSize=s;document.querySelectorAll('.size-btn').forEach(b=>b.classList.remove('sel'));el.classList.add('sel');}window.selectSize=selectSize;
function addFromModal(){if(!currentProduct)return;addToCart(currentProduct);closeModal();}window.addFromModal=addFromModal;
function addToCart(p){const ex=cart.find(c=>c.id===p.id);if(ex)ex.qty++;else cart.push({...p,qty:1,size:selectedSize||p.sizes[1]});updateCartUI();}
function removeFromCart(id){const i=cart.findIndex(c=>c.id===id);if(i>-1)cart.splice(i,1);updateCartUI();}window.removeFromCart=removeFromCart;
function updateCartUI(){const cnt=document.getElementById('cartCount');const tot=cart.reduce((s,c)=>s+c.qty,0);cnt.textContent=tot;cnt.classList.toggle('show',tot>0);const el=document.getElementById('cartItems');if(!cart.length){el.innerHTML='<div class="cart-empty">The runway awaits your selection</div>';}else{el.innerHTML=cart.map(c=>'<div class="cart-item"><div class="cart-thumb"></div><div class="cart-info"><div class="cart-name">'+c.name+(c.qty>1?' \u00d7 '+c.qty:'')+'</div><div class="cart-price">$'+(c.price*c.qty)+'</div></div><button class="cart-remove" onclick="removeFromCart(\''+c.id+'\')">\u2715</button></div>').join('');}document.getElementById('cartTotal').textContent='$'+cart.reduce((s,c)=>s+c.price*c.qty,0);}
function toggleCart(){document.getElementById('cart').classList.toggle('open');}window.toggleCart=toggleCart;
function checkout(){if(!cart.length)return;if(typeof wp!=='undefined'||document.querySelector('body.woocommerce')){const items=cart.map(c=>({id:c.sku,quantity:c.qty}));Promise.all(items.map(it=>fetch('/wp-json/wc/store/v1/cart/items',{method:'POST',headers:{'Content-Type':'application/json','Nonce':window.wcStoreApiNonce||''},body:JSON.stringify({id:it.id,quantity:it.quantity})}))).then(()=>window.location.href='/checkout').catch(()=>window.location.href='/checkout');}else{alert('SIGNATURE Order:\n'+cart.map(c=>c.name+' \u00d7 '+c.qty+' = $'+(c.price*c.qty)).join('\n')+'\n\nTotal: $'+cart.reduce((s,c)=>s+c.price*c.qty,0));}}window.checkout=checkout;
function launchAR(){alert('AR Experience launching...\nRequires mobile device with ARCore/ARKit.');}window.launchAR=launchAR;
function showView(idx){if(animating||idx===currentView)return;animating=true;currentView=idx;document.querySelectorAll('.room-btn').forEach((b,i)=>b.classList.toggle('active',i===idx));const tgt=VIEWS[idx],sp=camera.position.clone(),st=controls.target.clone(),dur=2400,start=performance.now();function av(now){const el=now-start,t=Math.min(el/dur,1);const e=t<.5?4*t*t*t:(t-1)*(2*t-2)*(2*t-2)+1;camera.position.lerpVectors(sp,tgt.p,e);controls.target.lerpVectors(st,tgt.t,e);controls.update();if(t<1)requestAnimationFrame(av);else animating=false;}requestAnimationFrame(av);}window.showView=showView;
function initGrain(){const c=document.getElementById('grain'),ctx=c.getContext('2d');c.width=256;c.height=256;(function draw(){const img=ctx.createImageData(256,256);for(let i=0;i<img.data.length;i+=4){const v=Math.random()*255;img.data[i]=img.data[i+1]=img.data[i+2]=v;img.data[i+3]=255;}ctx.putImageData(img,0,0);requestAnimationFrame(draw);})();}
function simulateLoading(){let p=0;const f=document.getElementById('loadFill');const iv=setInterval(()=>{p+=Math.random()*12+4;if(p>=100){p=100;clearInterval(iv);setTimeout(()=>{document.getElementById('loader').classList.add('done');['nav','rooms','info','cta'].forEach(id=>document.getElementById(id).classList.add('show'));},500);}f.style.width=p+'%';},180);}
function onResize(){camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);composer.setSize(innerWidth,innerHeight);}
function loop(){const t=clock.getElapsedTime();if(particles){particles.rotation.y=t*.006;const pos=particles.geometry.attributes.position;for(let i=0;i<pos.count;i++){pos.array[i*3+1]+=Math.sin(t*.3+i*.1)*.0005;if(pos.array[i*3+1]>12)pos.array[i*3+1]=0;}pos.needsUpdate=true;}
scene.traverse(o=>{if(o.userData.float){o.position.y=o.userData.float.baseY+Math.sin(t*o.userData.float.speed+o.userData.float.offset)*.2;o.rotation.y+=o.userData.float.rotSpeed*.003;o.rotation.x=Math.sin(t*.5)*.05;}if(o.userData.ringSpeed){o.rotation.z=t*o.userData.ringSpeed;}if(o.userData.mannequin){o.position.y=o.userData.mannequin.baseY+Math.sin(t*o.userData.mannequin.speed+o.userData.mannequin.offset)*.02;}});
controls.update();updateHotspots();composer.render();}
init();
