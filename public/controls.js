/* ---------- helper: some shared field definitions ---------- */
const SHARED = {
  subset_strategy : {type:"select",options:["random","artist_first5"],value:"random"},
  subset_size     : {type:"range",min:10,max:500,step:10,value:250},
  random_state    : {type:"range",min:0,max:999,step:1,value:42}
};

/* ---------- 1. DR_META : BASIC + ADVANCED ------------------ */
const DR_META = {

/* --------------------  UMAP  -------------------- */
UMAP : {
  basic : {
    n_neighbors:{type:"range",min:5,max:50,step:1,value:15},
    min_dist:{type:"range",min:0,max:0.4,step:0.01,value:0.1},
    metric:{type:"select",options:["euclidean","cosine","manhattan"],value:"euclidean"},
    n_components:{type:"range",min:2,max:3,step:1,value:2}
  },
  advanced : {
    spread:{type:"range",min:.5,max:2,step:.1,value:1},
    set_op_mix_ratio:{type:"range",min:.1,max:1,step:.1,value:.5},
    local_connectivity:{type:"range",min:1,max:5,step:1,value:1},
    ...SHARED
  },
  presets:{
    fast:{n_neighbors:10,min_dist:0.1,set_op_mix_ratio:1},
    detail:{n_neighbors:20,min_dist:0.05},
    edge_low_neighbors:{n_neighbors:2,min_dist:0},
    edge_high_neighbors:{n_neighbors:100,min_dist:0.99,metric:"cosine",spread:2}
  }
},

/* --------------------  t‑SNE  -------------------- */
"t‑SNE" : {
  basic : {
    perplexity:{type:"range",min:5,max:50,step:1,value:30},
    n_iter:{type:"range",min:250,max:1000,step:50,value:500},
    learning_rate:{type:"range",min:50,max:1000,step:10,value:200},
    n_components:{type:"range",min:2,max:3,step:1,value:2}
  },
  advanced : {
    early_exaggeration:{type:"range",min:8,max:32,step:1,value:12},
    early_exaggeration_iter:{type:"range",min:50,max:500,step:50,value:250},
    n_iter_without_progress:{type:"range",min:50,max:500,step:50,value:300},
    min_grad_norm:{type:"range",min:1e-8,max:1e-3,step:1e-8,value:1e-7},
    theta:{type:"range",min:0.1,max:0.8,step:0.05,value:0.5},
    negative_gradient_method:{type:"select",options:["fft","bh"],value:"fft"},
    initialization:{type:"select",options:["pca","random"],value:"pca"},
    n_jobs:{type:"range",min:1,max:8,step:1,value:1},
    metric:{type:"select",options:["euclidean","cosine"],value:"euclidean"},
    ...SHARED
  },
  presets:{
    fast:{perplexity:25,n_iter:500},
    edge_low_perplexity:{perplexity:5,learning_rate:10,n_iter:250,early_exaggeration:4,theta:0.1,initialization:"random"},
    edge_high_perplexity:{perplexity:100,learning_rate:1000,n_iter:1000,early_exaggeration:32,theta:0.8,negative_gradient_method:"bh"}
  }
},

/* ==========   Add the rest (PaCMAP, TriMAP, PHATE, …)  ========== */
/* --- Only two more shown here for brevity. Replicate pattern. --- */

PHATE : {
  basic : {
    knn:{type:"range",min:5,max:50,step:1,value:5},
    decay:{type:"range",min:2,max:60,step:1,value:40},
    n_components:{type:"range",min:2,max:3,step:1,value:2}
  },
  advanced:{
    t:{type:"select",options:["auto","local"],value:"auto"},
    gamma:{type:"range",min:0.01,max:4,step:0.01,value:1},
    ...SHARED
  },
  presets:{
    fast:{},
    practical_2:{knn:15,decay:20},
    edge_high_knn:{knn:50,gamma:0.1},
    edge_low_decay:{decay:2}
  }
},

TriMAP : {
  basic : {
    n_inliers:{type:"range",min:10,max:30,step:1,value:12},
    n_outliers:{type:"range",min:2,max:10,step:1,value:4},
    n_random:{type:"range",min:1,max:10,step:1,value:3},
    n_iters:{type:"range",min:200,max:1000,step:50,value:400},
    lr:{type:"range",min:0.05,max:0.2,step:0.01,value:0.1}
  },
  advanced:{
    weight_temp:{type:"range",min:0.1,max:1,step:0.05,value:0.5},
    distance:{type:"select",options:["euclidean","cosine","manhattan"],value:"euclidean"},
    opt_method:{type:"select",options:["dbd","sgd"],value:"dbd"},
    apply_pca:{type:"checkbox",value:true},
    n_dims:{type:"range",min:2,max:3,step:1,value:2},
    ...SHARED
  },
  presets:{
    fast:{},
    detail:{n_inliers:20,n_outliers:10,n_random:10,lr:0.05,n_iters:1000},
    safe_inliers_16:{n_inliers:16},
    safe_lr_0_05:{lr:0.05}
  }
},
/* --------------------  PaCMAP  -------------------- */
PaCMAP : {
  basic : {
    n_neighbors : {type:"range",min:1,max:30,step:1,value:10},
    num_iters   : {type:"range",min:200,max:1000,step:50,value:450},
    lr          : {type:"range",min:0.1,max:5,step:0.1,value:1},
    n_components: {type:"range",min:2,max:3,step:1,value:2}
  },
  advanced : {
    MN_ratio      : {type:"range",min:0.1,max:1,step:0.05,value:0.5},
    FP_ratio      : {type:"range",min:0.5,max:4,step:0.1,value:2},
    apply_pca     : {type:"checkbox",value:true},
    preprocess_pca: {type:"range",min:5,max:50,step:5,value:50},
    backend       : {type:"select",options:["annoy","hnswlib"],value:"annoy"},
    verbose       : {type:"checkbox",value:false},
    ...SHARED
  },
  presets : {
    fast:{},
    low_neighbors:{n_neighbors:2},
    pca20:{preprocess_pca:20},
    tiny_subset:{subset_size:40,n_neighbors:2}
  }
},

/* ----------------- ParamRepulsor (parametric‑UMAP) ---------------- */
ParamRepulsor : {
  basic : {
    n_neighbors : {type:"range",min:2,max:15,step:1,value:5},
    n_epochs    : {type:"range",min:100,max:600,step:50,value:300},
    lr          : {type:"range",min:0.1,max:5,step:0.1,value:1},
    n_components: {type:"range",min:2,max:3,step:1,value:2}
  },
  advanced : {
    spread            : {type:"range",min:0.5,max:2,step:0.1,value:1},
    repulsion_strength: {type:"range",min:0.5,max:2,step:0.1,value:1},
    apply_pca         : {type:"checkbox",value:true},
    init              : {type:"select",options:["pca","random"],value:"pca"},
    verbose           : {type:"checkbox",value:false},
    ...SHARED
  },
  presets : {
    fast:{},
    artist_first5:{subset_strategy:"artist_first5",subset_size:500}
  }
},

/* --------------------  t‑SNE‑PSO  -------------------- */
"t‑SNE‑PSO" : {
  basic : {
    perplexity   : {type:"range",min:5,max:50,step:1,value:30},
    n_iter       : {type:"range",min:250,max:1000,step:50,value:500},
    n_particles  : {type:"range",min:5,max:20,step:1,value:10},
    n_components : {type:"range",min:2,max:3,step:1,value:2}
  },
  advanced : {
    inertia_weight          : {type:"range",min:0.5,max:0.9,step:0.05,value:0.7},
    learning_rate           : {type:"range",min:50,max:1000,step:10,value:200},
    h                       : {type:"range",min:1e-22,max:1e-18,step:1e-22,value:1e-20},
    f                       : {type:"range",min:1e-22,max:1e-18,step:1e-22,value:1e-21},
    use_hybrid              : {type:"checkbox",value:true},
    dynamic_weight_adaptation:{type:"checkbox",value:true},
    parameter_optimization  : {type:"checkbox",value:true},
    small_dataset_handling  : {type:"checkbox",value:true},
    numerical_robustness    : {type:"checkbox",value:true},
    ...SHARED
  },
  presets : {
    default : {},
    shorter : {n_iter:400}
  }
},

/* --------------------  TSIMCNE  -------------------- */
TSIMCNE : {
  basic : {
    epoch_block1 : {type:"range",min:100,max:1000,step:50,value:500},
    epoch_block2 : {type:"range",min:10 ,max:500 ,step:10,value:50},
    epoch_block3 : {type:"range",min:100,max:1000,step:50,value:250},
    n_components : {type:"range",min:2,max:3,step:1,value:2}
  },
  advanced : { ...SHARED },
  presets : {
    default:{},
    shorter:{epoch_block1:400,epoch_block3:200}
  }
},

/* --------------------  SpaceMAP  -------------------- */
SpaceMAP : {
  basic : {
    n_near_field  : {type:"range",min:10,max:100,step:1,value:21},
    n_middle_field: {type:"range",min:20,max:80 ,step:1,value:50},
    eta           : {type:"range",min:0.01,max:1,step:0.05,value:0.6},
    n_epochs      : {type:"range",min:100,max:400,step:50,value:200},
    n_components  : {type:"range",min:2,max:3,step:1,value:2}
  },
  advanced : {
    d_local   : {type:"range",min:0,max:5,step:1,value:0},
    d_global  : {type:"range",min:1,max:10,step:0.5,value:4.5},
    init      : {type:"select",options:["spectral","random"],value:"spectral"},
    metric    : {type:"select",options:["euclidean","cosine"],value:"euclidean"},
    plot_results:{type:"checkbox",value:false},
    num_plots : {type:"range",min:0,max:100,step:5,value:50},
    verbose   : {type:"checkbox",value:true},
    ...SHARED
  },
  presets : {
    fast:{},
    practical_2:{n_near_field:25,n_middle_field:60,eta:0.8,n_epochs:400,verbose:false},
    edge_high_near:{n_near_field:100,n_middle_field:30,d_global:2,eta:0.5,n_epochs:150,init:"random",metric:"cosine"},
    edge_low_eta:{n_near_field:10,n_middle_field:80,d_local:2,d_global:10,eta:0.01,n_epochs:300,verbose:false}
  }
},

/* --------------------  SLISEmap  -------------------- */
SLISEmap : {
  basic : {
    radius       : {type:"range",min:1,max:5,step:0.1,value:3.5},
    lasso        : {type:"range",min:0.001,max:0.1,step:0.001,value:0.01},
    n_components : {type:"range",min:2,max:3,step:1,value:2}
  },
  advanced : {
    use_slipmap  : {type:"checkbox",value:false},
    ...SHARED
  },
  presets : {
    default:{},
    slipmap:{use_slipmap:true,radius:2}
  }
},

/* ---------------- Geodesic / Spectral group -------------------- */
Isomap : {
  basic : {
    n_neighbors  : {type:"range",min:2,max:20,step:1,value:5},
    n_components : {type:"range",min:2,max:3,step:1,value:2}
  },
  advanced : { ...SHARED },
  presets  : { basic:{}, edge_low:{n_neighbors:2}, edge_high:{n_neighbors:20} }
},

LLE : {
  basic : {
    n_neighbors  : {type:"range",min:2,max:30,step:1,value:15},
    n_components : {type:"range",min:2,max:3,step:1,value:2}
  },
  advanced : { ...SHARED },
  presets  : { basic:{}, edge_low:{n_neighbors:2}, edge_high:{n_neighbors:30} }
},

GLLE : {
  basic : {
    method       : {type:"select",options:["GLLE","GLLE_DirectSampling"],value:"GLLE"},
    k_neighbors  : {type:"range",min:5,max:30,step:1,value:10},
    max_iterations:{type:"range",min:10,max:200,step:10,value:50},
    n_components : {type:"range",min:2,max:3,step:1,value:2}
  },
  advanced : {
    n_generation_of_embedding:{type:"range",min:1,max:5,step:1,value:3},
    verbosity:{type:"checkbox",value:true},
    ...SHARED
  },
  presets : {
    glle_em_fast:{},
    glle_direct_long:{method:"GLLE_DirectSampling",k_neighbors:15,max_iterations:100,n_generation_of_embedding:5}
  }
},

Spectral : {
  basic : {
    n_neighbors  : {type:"range",min:2,max:30,step:1,value:10},
    n_components : {type:"range",min:2,max:3,step:1,value:2}
  },
  advanced : { ...SHARED },
  presets  : { basic:{}, edge_low:{n_neighbors:2}, edge_high:{n_neighbors:30} }
},

/* ---------------- Metric‑stress family -------------------- */
MDS : {
  basic : {
    max_iter     : {type:"range",min:100,max:1000,step:50,value:300},
    n_components : {type:"range",min:2,max:3,step:1,value:2}
  },
  advanced : { ...SHARED },
  presets  : { basic:{}, long:{max_iter:1000} }
},

Sammon : {
  basic : {
    n_iter       : {type:"range",min:100,max:1000,step:50,value:500},
    n_components : {type:"range",min:2,max:3,step:1,value:2}
  },
  advanced : {
    tol:{type:"range",min:1e-10,max:1e-5,step:1e-10,value:1e-9},
    ...SHARED
  },
  presets : { test_random:{n_iter:500} }
},

CLMDS : {
  basic : {
    n_clusters   : {type:"range",min:2,max:20,step:1,value:5},
    max_iter     : {type:"range",min:100,max:1000,step:50,value:300}
  },
  advanced : { ...SHARED },
  presets  : { default:{}, large_clusters:{n_clusters:10} }
},

/* ---------------- Linear / kernel projections ------------------ */
PCA : {
  basic : { n_components:{type:"range",min:2,max:50,step:1,value:2} },
  advanced : { ...SHARED },
  presets:{ fast:{} }
},

IPCA : {
  basic : { n_components:{type:"range",min:2,max:50,step:1,value:2} },
  advanced : {
    batch_size:{type:"range",min:50,max:500,step:50,value:200},
    ...SHARED
  },
  presets:{ fast:{} }
},

SVD : {
  basic : { n_components:{type:"range",min:2,max:50,step:1,value:2} },
  advanced : { ...SHARED },
  presets:{ fast:{} }
},

FA : {
  basic : { n_components:{type:"range",min:2,max:50,step:1,value:2} },
  advanced : { ...SHARED },
  presets:{ fast:{} }
},

ICA : {
  basic : { 
    n_components:{type:"range",min:2,max:50,step:1,value:2},
    max_iter   :{type:"range",min:200,max:1000,step:100,value:500}
  },
  advanced : { ...SHARED },
  presets:{ fast:{}, iter_1000:{max_iter:1000} }
},

DictLearn : {
  basic : { 
    n_components:{type:"range",min:2,max:50,step:1,value:2},
    max_iter   :{type:"range",min:100,max:1000,step:100,value:300}
  },
  advanced : { ...SHARED },
  presets:{ fast:{} }
},

"Kernel‑PCA" : {
  basic : { 
    n_components:{type:"range",min:2,max:50,step:1,value:2},
    kernel     :{type:"select",options:["rbf","poly","sigmoid","linear"],value:"rbf"}
  },
  advanced : {
    gamma:{type:"range",min:0.01,max:10,step:0.01,value:1},
    fit_inverse_transform:{type:"checkbox",value:true},
    ...SHARED
  },
  presets:{ fast:{}, gamma_0_1:{gamma:0.1} }
},

"Nyström‑PCA" : {
  basic : { 
    n_components       :{type:"range",min:2,max:50,step:1,value:2},
    nystroem_components:{type:"range",min:50,max:2000,step:50,value:200}
  },
  advanced : {
    kernel:{type:"select",options:["rbf","poly","sigmoid","linear"],value:"rbf"},
    gamma :{type:"range",min:0.01,max:10,step:0.01,value:1},
    ...SHARED
  },
  presets:{ fast:{} }
},

GRP : {
  basic : { n_components:{type:"range",min:2,max:50,step:1,value:2} },
  advanced : {
    eps:{type:"range",min:0.05,max:0.5,step:0.05,value:0.1},
    ...SHARED
  },
  presets:{ fast:{}, eps_0_3:{eps:0.3} }
},

SRP : {
  basic : { n_components:{type:"range",min:2,max:50,step:1,value:2} },
  advanced : {
    density:{type:"range",min:0.01,max:1,step:0.05,value:0.5},
    eps    :{type:"range",min:0.05,max:0.5,step:0.05,value:0.1},
    ...SHARED
  },
  presets:{ fast:{}, density_sparse:{density:0.05} }
},

/* ---------------- Simple clustering baseline ------------------ */
Agg : {
  basic : { n_clusters:{type:"range",min:2,max:10,step:1,value:2} },
  advanced : { ...SHARED },
  presets : { fast:{} }
}


};  /* ---------- END DR_META ----------------- */

/* ====================================================================
   2. Build the accordion UI
   ==================================================================== */
const container=document.getElementById("panel");

Object.entries(DR_META).forEach(([algo, cfg])=>{
  const wrap=document.createElement("details");
  wrap.innerHTML=`<summary>${algo}</summary>`;
  /* preset bar */
  const presetBar=document.createElement("div");
  presetBar.className="preset-bar";
  Object.entries(cfg.presets).forEach(([pname,vals])=>{
    const b=document.createElement("button");
    b.textContent=pname;
    b.onclick=()=>applyPreset(algo,vals);
    presetBar.appendChild(b);
  });
  wrap.appendChild(presetBar);

  /* helper to make one row */
  const makeRow=(param,def,scope)=>{
    const row=document.createElement("div");
    row.className="param-row";
    row.innerHTML=`<label for="${algo}_${scope}_${param}">${param}</label>`;
    let inp;
    if(def.type==="select"){
      inp=document.createElement("select");
      def.options.forEach(o=>{
        const opt=document.createElement("option"); opt.value=opt.textContent=o; inp.appendChild(opt);
      });
      inp.value=def.value;
    }else if(def.type==="checkbox"){
      inp=document.createElement("input"); inp.type="checkbox"; inp.checked=def.value;
    }else{ /* range */
      inp=document.createElement("input"); inp.type="range";
      Object.assign(inp,{min:def.min,max:def.max,step:def.step,value:def.value});
    }
    inp.id=`${algo}_${scope}_${param}`;
    inp.dataset.algo=algo; inp.dataset.param=param;
    row.appendChild(inp);
    if(def.type==="range"){
      const out=document.createElement("output"); out.textContent=inp.value;
      inp.oninput=()=>out.textContent=inp.value; row.appendChild(out);
    }
    return row;
  };

  /* basic params */
  Object.entries(cfg.basic).forEach(([p,d])=>wrap.appendChild(makeRow(p,d,"b")));

  /* advanced accordion */
  const advDetails=document.createElement("details");
  advDetails.className="adv";
  advDetails.innerHTML="<summary>Advanced</summary>";
  Object.entries(cfg.advanced).forEach(([p,d])=>advDetails.appendChild(makeRow(p,d,"a")));
  wrap.appendChild(advDetails);

  container.appendChild(wrap);
});

/* ====================================================================
   3. Helper functions
   ==================================================================== */
function applyPreset(algo,vals){
  Object.entries(vals).forEach(([p,v])=>{
    ["b","a"].forEach(scope=>{
      const el=document.getElementById(`${algo}_${scope}_${p}`);
      if(el){
        if(el.type==="checkbox") el.checked=v;
        else el.value=v;
        el.dispatchEvent(new Event("input"));
      }
    });
  });
}

function getConfig(){
  const out={};
  document.querySelectorAll("[data-algo]").forEach(el=>{
    const {algo,param}=el.dataset;
    if(!out[algo]) out[algo]={};
    out[algo][param]=(el.type==="checkbox")?el.checked:parseFloat(el.value)||el.value;
  });
  return out;
}