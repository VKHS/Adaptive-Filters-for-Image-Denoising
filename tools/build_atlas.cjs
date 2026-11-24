// Rebuild the supplemental SVG atlas and its synthetic score table. Node.js 18+; no dependencies.
// Standalone reduced-size educational examples; original Python/MATLAB benchmark code is unchanged.
function generate(csv) {
  const out={}, base="figures/atlas/", W=96,H=64,N=W*H, pi=Math.PI;
  const ink="#172c43", muted="#52677a", blue="#2466a2", teal="#007f76", orange="#bc641c", purple="#7853a8", red="#b34453", light="#f4f8fb";
  const esc=s=>String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
  const text=(x,y,s,size=18,fill=ink,weight=400,anchor="start")=>`<text x="${x}" y="${y}" font-family="Arial,Helvetica,sans-serif" font-size="${size}" fill="${fill}" font-weight="${weight}" text-anchor="${anchor}">${esc(s)}</text>`;
  const rect=(x,y,w,h,fill,stroke="none",r=0)=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="${fill}" stroke="${stroke}"/>`;
  const line=(x1,y1,x2,y2,col=ink,dash="")=>`<path d="M${x1} ${y1}L${x2} ${y2}" fill="none" stroke="${col}" stroke-width="2"${dash?' stroke-dasharray="'+dash+'"':""}/>`;
  const arrow=(x1,y1,x2,y2,col=ink)=>`<path d="M${x1} ${y1}L${x2} ${y2}" fill="none" stroke="${col}" stroke-width="2" marker-end="url(#arrow)"/>`;
  const svg=(w,h,title,desc,body)=>`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" role="img"><title>${esc(title)}</title><desc>${esc(desc)}</desc><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="${ink}"/></marker></defs>${rect(0,0,w,h,"#ffffff")}${body}</svg>\n`;
  const header=(tag,title,sub)=>rect(0,0,1100,8,teal)+text(30,37,tag,15,teal,700)+text(30,69,title,27,ink,700)+text(30,97,sub,16,muted);
  const block=(x,y,w,h,lines,c)=>{let q=rect(x,y,w,h,c+"15",c,9);lines.forEach((s,i)=>q+=text(x+w/2,y+h/2+(i-(lines.length-1)/2)*19+5,s,i===0?16:13,c,i===0?700:400,"middle"));return q};
  const map=(fn)=>Float64Array.from({length:N},(_,k)=>fn(Math.floor(k/W),k%W,k));
  const mean=a=>a.reduce((s,v)=>s+v,0)/a.length;
  const variance=a=>{let m=mean(a);return mean(a.map(v=>(v-m)**2))};
  const clip=v=>Math.min(1,Math.max(0,v));
  const psnr=(a,b)=>-10*Math.log10(mean(a.map((v,k)=>(v-clip(b[k]))**2)));
  const median=a=>{let q=Array.from(a).sort((a,b)=>a-b), n=q.length;return (q[(n-1)>>1]+q[n>>1])/2};
  const rng=(seed)=>{let s=seed>>>0;return ()=>{s=(Math.imul(1664525,s)+1013904223)>>>0;return(s+.5)/4294967296}};
  const randn=r=>Math.sqrt(-2*Math.log(r()))*Math.cos(2*pi*r());
  const refidx=(i,n)=>{const p=2*n-2;let a=((i%p)+p)%p;return a<n?a:p-a};
  const at=(a,i,j)=>a[refidx(i,H)*W+refidx(j,W)];
  const scene=map((i,j)=>clip(.24+.13*j/W+.12*i/H+.22*(j>14&&j<42&&i>9&&i<48)+.28*((i-39)**2+(j-70)**2<14**2)+.045*Math.sin(2*pi*j/19)*(i>44)+.06*Math.exp(-((i-12)**2+(j-72)**2)/120)));
  const smooth=map((i,j)=>.32+.15*j/W+.10*i/H+.15*Math.exp(-((i-30)**2+(j-40)**2)/420));
  const lattice=map((i,j)=>.5+.15*Math.cos(2*pi*(i/9+j/13))+.12*Math.cos(2*pi*(i/15-j/8)));
  const metrics=[];
  // Reference sinusoid, two-pass raster LMS, mean removed/restored (known frequency).
  const aNoisy=map((i,j,k)=>scene[k]+.14*Math.cos(2*pi*(i/16+j/9)+.7));
  const aOut=new Float64Array(N), am=mean(aNoisy);let wa=[0,0];
  for(let p=0;p<2;p++)for(let k=0;k<N;k++){let i=Math.floor(k/W),j=k%W,t=2*pi*(i/16+j/9),x=[Math.cos(t),Math.sin(t)],e=aNoisy[k]-am-wa[0]*x[0]-wa[1]*x[1];wa[0]+=.001*e*x[0];wa[1]+=.001*e*x[1];aOut[k]=e+am}
  // Interline sign update and Gaussian high-pass of estimated offsets.
  let rb=rng(22), offsets=Float64Array.from({length:H},()=>.07*randn(rb));
  const bNoisy=map((i,j,k)=>scene[k]+offsets[i]);
  const bOut=bNoisy.slice(), bo=new Float64Array(H);
  for(let i=1;i<H;i++){let b=0;for(let p=0;p<2;p++)for(let j=0;j<W;j++){let e=bNoisy[i*W+j]-bOut[(i-1)*W+j]-b;b+=.002*Math.sign(e)}bo[i]=b;for(let j=0;j<W;j++)bOut[i*W+j]-=b}
  function gaussian1(a, sigma, boundary="reflect") {let r=Math.round(4*sigma),g=Array.from({length:2*r+1},(_,k)=>Math.exp(-.5*((k-r)/sigma)**2)), norm=g.reduce((s,v)=>s+v,0);const ix=(i,n)=>{if(boundary==="reflect")return refidx(i,n);let p=2*n,q=((i%p)+p)%p;return q<n?q:p-1-q};return a.map((_,i)=>g.reduce((s,v,k)=>s+v*a[ix(i+k-r,a.length)],0)/norm)}
  const bs=gaussian1(bo,8);for(let k=0;k<N;k++)bOut[k]+=bs[Math.floor(k/W)];
  // Scenario C: row-mean removal, Gaussian high-band, delayed FIR LMS, subtract from original.
  const cNoisy=map((i,j,k)=>smooth[k]+.15*Math.cos(2*pi*j/9+.3));
  const high=new Float64Array(N);
  for(let i=0;i<H;i++){let row=cNoisy.slice(i*W,(i+1)*W),m=mean(row);row=row.map(v=>v-m);let low=gaussian1(row,4,"symmetric");for(let j=0;j<W;j++)high[i*W+j]=row[j]-low[j]}
  const L=32,delay=8,cmu=.015/(L*variance(high)),cw=new Float64Array(L),cOut=new Float64Array(N);
  for(let k=0;k<N;k++){let i=Math.floor(k/W),j=k%W,y=0;for(let t=0;t<L;t++)y+=cw[t]*at(high,i,j-delay-t);let e=high[k]-y;for(let t=0;t<L;t++)cw[t]+=cmu*e*at(high,i,j-delay-t);cOut[k]=cNoisy[k]-y}
  // Scenario Dg: robust-scale gate, frozen source per pass, original target each pass.
  let rd=rng(33);const dNoisy=scene.map(v=>rd()<.09?rd():v);
  function taps(r,h){let a=[];for(let i=-r;i<=r;i++)for(let j=-r;j<=r;j++)if(Math.max(Math.abs(i),Math.abs(j))>h)a.push([i,j]);return a}
  const dt=taps(2,0),dm=median(dNoisy),dz=dNoisy.map(v=>v-dm),dmu=.01/(dt.length*variance(dz.map(v=>Math.max(-.5,Math.min(.5,v))))),dw=new Float64Array(dt.length).fill(1/dt.length);
  let src=dz.slice(),dOut=dz.slice(),flags=new Uint8Array(N);
  for(let p=0;p<3;p++){let s=.05;for(let k=0;k<N;k++){let i=Math.floor(k/W),j=k%W,y=0;for(let t=0;t<dt.length;t++)y+=dw[t]*at(src,i+dt[t][0],j+dt[t][1]);let e=dz[k]-y,bad=Math.abs(e)>Math.max(4*s,.1);flags[k]=+bad;if(bad)dOut[k]=y;else{dOut[k]=dz[k];for(let t=0;t<dt.length;t++)dw[t]+=dmu*e*at(src,i+dt[t][0],j+dt[t][1]);s+=.01*(1.4826*Math.abs(e)-s)}}src=dOut.slice()}dOut=dOut.map(v=>v+dm);
  // Scenario E: larger 2-D blind-spot predictor on a lattice plus white noise, h=0 explicitly.
  let re=rng(44);const eNoisy=lattice.map(v=>v+.15*randn(re)), em=mean(eNoisy),ez=eNoisy.map(v=>v-em),et=taps(4,0),ew=new Float64Array(et.length),emu=.025/(et.length*variance(ez)),eOut=new Float64Array(N);
  for(let p=0;p<2;p++)for(let k=0;k<N;k++){let i=Math.floor(k/W),j=k%W,y=0;for(let t=0;t<et.length;t++)y+=ew[t]*at(ez,i+et[t][0],j+et[t][1]);let e=ez[k]-y;for(let t=0;t<et.length;t++)ew[t]+=emu*e*at(ez,i+et[t][0],j+et[t][1]);eOut[k]=y+em}
  // Scenario F: independent dark calibration, scalar LMS optical-black weight, 16 reference pixels.
  let rf=rng(55);const row=Float64Array.from({length:H},()=>.075*randn(rf)),darkRow=Float64Array.from({length:H},()=>.075*randn(rf));
  const optical=a=>a.map(v=>{let sum=0;for(let q=0;q<16;q++)sum+=v+.015*randn(rf);return sum/16});
  const ob=optical(row),dob=optical(darkRow),dark=map((i)=>darkRow[i]+.01*randn(rf)),fNoisy=map((i,j,k)=>scene[k]+row[i]+.01*randn(rf));let fw=0;
  for(let p=0;p<3;p++)for(let k=0;k<N;k++){let x=dob[Math.floor(k/W)];fw+=.5*(dark[k]-fw*x)*x}
  const fOut=map((i,j,k)=>fNoisy[k]-fw*ob[i]);
  const specs=[
    {id:"A",title:"Adaptive notch | synthetic reference",sub:"Known spatial frequency; two quadrature weights learn amplitude and phase.",steps:[["Plane-wave reference","cos θ, sin θ",orange],["Adaptive dot product","wᵀx = interference",purple],["Subtract from primary","e = d − y",blue],["Keep error e","restored image",teal]],note:"Feedback: error e updates w; image mean is removed and restored.",param:"Known (u,v) = (1/16, 1/9); μ₂ = .001; 2 raster passes",clean:scene,noisy:aNoisy,est:aOut},
    {id:"B",title:"Bias / drift | interline adaptation",sub:"Predict the row offset relative to the previous corrected row, not the scene.",steps:[["Adjacent rows","dᵢ − corrected dᵢ₋₁",blue],["Sign-error update","constant-reference bᵢ",purple],["High-pass offsets","bᵢ − Gaussian(b)ᵢ",orange],["Subtract offset","one value per row",teal]],note:"Slow vertical shading is restored; row 0 is the anchor.",param:"Sign step .002; 2 sweeps per row; Gaussian σ = 8 rows",clean:scene,noisy:bNoisy,est:bOut},
    {id:"C",title:"No-reference periodic canceller",sub:"A high-band split protects low-frequency scene content from the delayed predictor.",steps:[["Row high band","z − Gaussian(z)",blue],["Delayed FIR taps","d[n−Δ−k]",orange],["Adaptive predictor","y = predictable high band",purple],["Keep d − y","low band + high-band error",teal]],note:"LMS feedback uses high-band error, not the complete-image residual.",param:"L = 32; Δ = 8; α = .015; split σ = 4 px (small-demo settings)",clean:smooth,noisy:cNoisy,est:cOut},
    {id:"D",title:"Self-tuning | error-gated blind spot",sub:"Predict the centre from surrounding taps; gate both replacement and adaptation.",steps:[["5 × 5 neighbourhood","centre excluded",blue],["Adaptive prediction","y = wᵀx",purple],["Error detector","|d − y| > max(4s, 0.1)?",orange],["Select d or y","flagged → y; else d",teal]],note:"Only accepted pixels update weights and scale; later passes reuse restored neighbours.",param:"9% random replacements; r = 2; h = 0; α = .01; k = 4; threshold floor 0.1; 3 passes",clean:scene,noisy:dNoisy,est:dOut},
    {id:"E",title:"Adaptive line enhancer | preserve predictable signal",sub:"An expanded blind-spot filter predicts coherent structure instead of cancelling it.",steps:[["Estimate correlation","choose central hole h",orange],["Spatial tap vector","window minus hole",blue],["Adaptive predictor","y = wᵀx",purple],["Keep prediction y","restore image mean",teal]],note:"In this white-noise example h is set to zero; correlated noise may need a larger hole.",param:"Lattice + σ = .15 white noise; r = 4; h = 0; α = .025; 2 passes",clean:lattice,noisy:eNoisy,est:eOut},
    {id:"F",title:"Reference sensor | dark-frame calibration",sub:"A separate observation of the row interference makes it identifiable.",steps:[["Dark frame + OB","independent calibration",orange],["Train scalar w","LMS on dark pixels",purple],["Scene + row OB mean","freeze calibrated w",blue],["Subtract w·OB","keep error output",teal]],note:"Optical-black pixels (OB) are simulated; no physical sensor measurement is claimed.",param:"16 OB samples per row; μ₂ = .5; 3 dark passes; independent scene",clean:scene,noisy:fNoisy,est:fOut}
  ];
  // Quantized display only; all scores use full-resolution unquantized float data.
  function raster(a,x,y,ww,hh,max=1){let paths=Array.from({length:32},()=>[]);for(let i=0;i<H;i++){let j=0;while(j<W){let c=Math.round(31*clip(a[i*W+j]/max)),q=j+1;while(q<W&&Math.round(31*clip(a[i*W+q]/max))===c)q++;paths[c].push(`M${j} ${i}h${q-j}v1h-${q-j}z`);j=q}}let s=`<svg x="${x}" y="${y}" width="${ww}" height="${hh}" viewBox="0 0 ${W} ${H}" shape-rendering="crispEdges">`;paths.forEach((p,k)=>{if(p.length){let v=Math.round(255*k/31).toString(16).padStart(2,"0");s+=`<path fill="#${v}${v}${v}" d="${p.join("")}"/>`}});return s+"</svg>"+rect(x,y,ww,hh,"none","#c9d5df") }
  for(const s of specs){let p=psnr(s.clean,s.noisy),q=psnr(s.clean,s.est);if(!Number.isFinite(p+q))throw Error(s.id+" nonfinite");metrics.push({scenario:s.id,psnr_input:p,psnr_output:q,gain:q-p});
    let body=header("SCENARIO "+s.id+"  /  IMPLEMENTATION ATLAS",s.title,s.sub);
    body+=rect(25,118,1050,126,light,"#dbe5ed",10);
    s.steps.forEach((b,i)=>{let x=42+i*258;body+=block(x,139,237,58,b.slice(0,2),b[2]);if(i<3)body+=arrow(x+237,168,x+258,168)});
    body+=text(43,225,s.note,15,muted);
    body+=text(30,273,"CONTROLLED SYNTHETIC EXAMPLE",15,teal,700)+text(30,296,s.param,15,muted);
    const panels=[["Clean target",s.clean,1],["Corrupted input",s.noisy,1],["Adaptive output",s.est,1],["Removed: input − output",s.noisy.map((v,k)=>clip(.5+2*(v-s.est[k]))),1],["Absolute output error",s.est.map((v,k)=>Math.abs(clip(v)-s.clean[k])),.25]];
    panels.forEach((z,i)=>{let x=30+i*210;body+=text(x,327,z[0],14,ink,700)+raster(z[1],x,338,196,131,z[2]);body+=text(x,492,i===0?"Intensity [0,1]":i===1?`${p.toFixed(2)} dB PSNR`:i===2?`${q.toFixed(2)} dB PSNR`:i===3?"Signed, grey = 0, ±0.25":"Error display [0, 0.25]",14,i===2?teal:muted,i===2?700:400)});
    body+=rect(30,512,1040,50,"#eaf5f2","none",8)+text(46,542,`ΔPSNR ${q-p>=0?"+":""}${(q-p).toFixed(2)} dB  •  96 × 64 synthetic pixels  •  compact re-implementation of the core equations`,16,teal,700);
    out[base+s.id+"_implementation.svg"]=svg(1100,585,s.title,s.sub,body);
  }
  // Reference taxonomy; deliberately separates estimation target from update error.
  let body=header("DESIGN MAP","Six adaptive configurations, three reference families","Select by the available reference and whether the predictable component is signal or interference.");
  const rows=[["A","Synthetic sinusoid","Periodic noise","Error  e = d − y",orange],["B","Constant / previous row","Row offset","Corrected primary",orange],["C","Delayed high band","Predictable interference","Error + preserved low band",purple],["D","Blind-spot neighbours","Predictable scene","Prediction y / gated selection",blue],["E","Larger blind-spot window","Predictable scene","Prediction y",blue],["F","Independent sensor","Correlated interference","Error  e = d − y",teal]];
  const cols=[42,122,455,780];["ID","Reference source","What the filter estimates","What is retained"].forEach((v,i)=>body+=text(cols[i],143,v,15,muted,700));
  rows.forEach((r,i)=>{let y=160+i*63;body+=rect(28,y,1044,54,i%2?"#f4f8fb":"#eaf0f5","none",8)+rect(38,y+9,47,36,r[4],"none",8)+text(61,y+33,r[0],19,"white",700,"middle")+text(122,y+32,r[1],17,ink,700)+text(455,y+32,r[2],17,ink)+text(780,y+32,r[3],16,teal,700)});
  body+=text(30,565,"Key distinction: LMS always uses prediction error for learning; the application need not keep that error.",16,muted,700);
  out[base+"reference_taxonomy.svg"]=svg(1100,590,"Reference taxonomy","The six configurations grouped by reference, predicted component, and retained output",body);
  // Geometric comparison of 2-D predictor tap masks.
  body=header("SPATIAL ADAPTATION","From scalar delay to a 2-D blind spot","The central square is excluded from the input vector; only the surrounding taps feed the predictor.");
  const masks=[{r:2,h:0,name:"D · 5 × 5",note:"White noise / gated impulses"},{r:3,h:0,name:"E · 7 × 7",note:"Larger predictive support"},{r:4,h:2,name:"E · 9 × 9",note:"5 × 5 excluded region"}];
  masks.forEach((m,k)=>{let cx=190+k*360, n=2*m.r+1,s=26,x=cx-n*s/2,y=173;body+=text(cx,145,m.name,20,ink,700,"middle");for(let i=-m.r;i<=m.r;i++)for(let j=-m.r;j<=m.r;j++){let c=Math.max(Math.abs(i),Math.abs(j))<=m.h?"#f7d8b6":"#91c3df";if(i===0&&j===0)c=red;body+=rect(x+(j+m.r)*s,y+(i+m.r)*s,s-2,s-2,c,"none",3)}let L=n*n-(2*m.h+1)**2;body+=text(cx,431,`${L} taps  ·  r=${m.r}, h=${m.h}`,18,teal,700,"middle")+text(cx,457,m.note,15,muted,400,"middle")});
  body+=rect(45,490,20,20,"#91c3df","none",3)+text(73,506,"active tap",15,muted)+rect(265,490,20,20,"#f7d8b6","none",3)+text(293,506,"excluded region",15,muted)+rect(536,490,20,20,red,"none",3)+text(564,506,"target pixel",15,muted)+text(30,550,"L = (2r + 1)² − (2h + 1)²; larger holes reduce noise leakage but also remove useful nearby context.",16,ink,700);
  out[base+"blindspot_geometry.svg"]=svg(1100,575,"Blind-spot tap geometry","5 by 5 and 7 by 7 windows excluding center and 9 by 9 window excluding 5 by 5 square",body);
  // Committed benchmark data, not new experiments.
  const parse=line=>line.match(/("(?:[^"]|"")*"|[^,]*)(,|$)/g).filter(x=>x!=="").map(x=>x.replace(/,$/,"").replace(/^"|"$/g,"").replace(/""/g,'"'));
  const data=csv.trim().split(/\r?\n/).slice(1).map(l=>{const a=parse(l);return {noise:a[0],method:a[1],psnr:+a[2],ssim:+a[3],gain:+a[4]}});
  const methods=["A","B","C","D","Dg","E","F","median3","AMF","Wiener5"], names=["Gaussian white","Gaussian correlated","Poisson","Blur + noise","Salt & pepper","Random impulses","Burst impulses","Pixel RTS","Readout RTS","Periodic interference","Row banding"],keys=["gaussian","correlated","poisson","blur","salt_pepper","impulse","burst","telegraph_pixel","telegraph_readout","periodic","banding"];
  body=header("ORIGINAL BENCHMARK / PSNR","Noise–method compatibility","Gain relative to the noisy input (dB). Negative gains and unavailable references are shown explicitly.");
  let x0=245, cw2=81,y0=154,ch=44;methods.forEach((m,i)=>body+=text(x0+cw2*i+cw2/2,y0-10,m,14,ink,700,"middle"));
  keys.forEach((k,i)=>{body+=text(30,y0+i*ch+28,names[i],15,ink,500);methods.forEach((m,j)=>{let d=data.find(z=>z.noise===k&&z.method===m);if(!d)throw Error("missing "+k+" "+m);let g=d.gain, c=!Number.isFinite(g)?"#e6ebef":g<-.05?"#f4c6c9":g<.05?"#f2f5f8":g<2?"#d9efea":g<6?"#a0d5cb":g<12?"#4ba99a":"#11786e";let t=!Number.isFinite(g)?"n/a":Math.abs(g)<.05?"0.0":(g>0?"+":"")+g.toFixed(1);body+=rect(x0+j*cw2,y0+i*ch,cw2-3,ch-3,c,"none",4)+text(x0+j*cw2+(cw2-3)/2,y0+i*ch+26,t,14,g>=12?"white":ink,700,"middle")})});
  body+=text(30,665,"Red = degradation   •   Grey = unavailable reference   •   Darker teal = larger improvement",15,muted)+text(30,694,"Source: results/benchmark_python.csv; 512 × 512 camera image, fixed default settings, one stored run.",15,muted);
  out[base+"benchmark_gain.svg"]=svg(1100,720,"PSNR gain matrix","Stored benchmark gains for 11 corruption models and 10 methods",body);
  // Paired PSNR / SSIM progression from the recorded cascade.
  const st=data.filter(d=>d.noise==="mixed"&&d.method.startsWith("stage"));if(st.length!==6)throw Error("cascade rows "+st.length);
  body=header("ORIGINAL BENCHMARK / MIXED CORRUPTIONS","Cascade progression: PSNR and SSIM","Physical reference channels first; deterministic, sparse and broadband disturbances follow.");
  const labs=["Input","F · row","F · readout","A · notch","D · gated","E · enhancer"];
  const plot=(x,y,w,h,lo,hi,vals,labels,col,title,ticks)=>{let z=text(x,y-15,title,20,col,700), px=i=>x+48+i*(w-70)/5,py=v=>y+h-45-(v-lo)/(hi-lo)*(h-65);ticks.forEach(t=>{z+=line(x+48,py(t),x+w-10,py(t),"#dbe4eb")+text(x+39,py(t)+5,String(t),12,muted,400,"end")});z+=`<path d="${vals.map((v,i)=>(i?"L":"M")+px(i)+" "+py(v)).join("")}" fill="none" stroke="${col}" stroke-width="3"/>`;vals.forEach((v,i)=>{z+=`<circle cx="${px(i)}" cy="${py(v)}" r="5" fill="${col}"/>`+text(px(i),py(v)-12,labels[i],13,col,700,"middle")+text(px(i),y+h-12,labs[i].split(" · ")[0]+(i===1?" row":i===2?" ref":i===4?" gated":i===5?" ALE":""),12,ink,500,"middle")});return z};
  body+=plot(32,151,500,300,16,28,st.map(z=>z.psnr),st.map(z=>z.psnr.toFixed(2)),blue,"PSNR (dB)",[16,20,24,28]);
  body+=plot(565,151,500,300,0,.8,st.map(z=>z.ssim),st.map(z=>z.ssim.toFixed(3)),teal,"SSIM",[0,.2,.4,.6,.8]);
  body+=rect(30,477,1040,63,"#eaf5f2","none",8)+text(46,503,`Total: +${(st[5].psnr-st[0].psnr).toFixed(2)} dB PSNR  ·  SSIM ${st[0].ssim.toFixed(3)} → ${st[5].ssim.toFixed(3)}`,20,teal,700)+text(46,525,"Cumulative stages, not an ablation; order and side information matter.",15,muted);
  body+=text(30,570,"Source: committed benchmark CSV. F receives simulated synchronized side information; blur inversion is not used.",15,muted);
  out[base+"cascade_progress.svg"]=svg(1100,595,"Mixed-noise cascade","Stored PSNR and SSIM for all six cumulative stages",body);
  // Theory visual: reference purity and primary noise floor, exact expression.
  body=header("REFERENCE QUALITY / THEORY","How a noisy reference limits cancellation","Scalar Wiener model with independent primary-only and reference-only noise.");
  const X=100,Y=138,PW=900,PH=340; const xs=Array.from({length:121},(_,i)=>-4+4*i/120);let vx=v=>X+(v+4)*PW/4,vy=v=>Y+PH-v*PH/40;
  for(let i=0;i<=4;i++){body+=line(vx(-4+i),Y,vx(-4+i),Y+PH,"#dce5ec")+text(vx(-4+i),Y+PH+24,["10⁻⁴","10⁻³","10⁻²","10⁻¹","1"][i],15,muted,400,"middle")}
  for(let i=0;i<=40;i+=10)body+=line(X,vy(i),X+PW,vy(i),"#dce5ec")+text(X-12,vy(i)+5,i+" dB",14,muted,400,"end");
  [[.001,blue],[.01,teal],[.1,orange]].forEach(([p,c],i)=>{let points=xs.map(v=>{let r=10**v;return [vx(v),vy(10*Math.log10((1+p)/(p+r/(1+r))))]});body+=`<path d="${points.map(([a,b],j)=>(j?"L":"M")+a.toFixed(1)+" "+b.toFixed(1)).join("")}" fill="none" stroke="${c}" stroke-width="3"/>`+line(200+i*260,566,235+i*260,566,c)+text(243+i*260,571,`R_primary = ${p}`,15,c,700)});
  body+=text(550,534,"Reference-only / correlated noise power ratio",17,ink,700,"middle")+text(30,603,"Analytical curve: NR = (1 + R_primary) / (R_primary + R_reference / (1 + R_reference)).",15,muted);
  out[base+"reference_quality.svg"]=svg(1100,625,"Reference purity and theoretical noise reduction","Analytical curves for three primary noise floors",body);
  // check file content and numeric evidence before creating any Git object.
  if(Object.keys(out).length!==11)throw Error("unexpected SVG count "+Object.keys(out).length);
  out["results/atlas_synthetic.csv"]="scenario,psnr_input_db,psnr_output_db,gain_db\n"+metrics.map(m=>[m.scenario,m.psnr_input.toFixed(4),m.psnr_output.toFixed(4),m.gain.toFixed(4)].join(",")).join("\n")+"\n";
  return {out,metrics,st};
}
const fs=require('node:fs'), path=require('node:path');
const root=path.resolve(__dirname,'..');
const {out,metrics}=generate(fs.readFileSync(path.join(root,'results/benchmark_python.csv'),'utf8'));
for(const [file,contents] of Object.entries(out)){const p=path.join(root,file);fs.mkdirSync(path.dirname(p),{recursive:true});fs.writeFileSync(p,contents);}
console.table(metrics);
