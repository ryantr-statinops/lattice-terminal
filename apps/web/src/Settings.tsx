import {useEffect,useState} from 'react';
import {useLocation,useNavigate} from 'react-router-dom';
import {PageHeader} from './ui/layout';
import {SettingsSidebar,type SettingsCategory} from './settings/SettingsSidebar';
import {AppearanceTab} from './settings/AppearanceTab';
import {ColorsTab} from './settings/ColorsTab';
import {SourcesTab} from './settings/SourcesTab';
import {ProfileTab} from './settings/ProfileTab';

export function Settings(){
  const {hash}=useLocation();
  const navigate=useNavigate();

  const getCategoryFromHash=(h:string):SettingsCategory=>{
    if(h==='#colors'||h==='#appearance-colors')return 'colors';
    if(h==='#sources')return 'sources';
    if(h==='#profile')return 'profile';
    return 'appearance';
  };

  const [activeCategory,setActiveCategory]=useState<SettingsCategory>(()=>getCategoryFromHash(hash));

  useEffect(()=>{
    const next=getCategoryFromHash(hash);
    if(next!==activeCategory){
      setActiveCategory(next);
    }
  },[hash,activeCategory]);

  const handleSelect=(category:SettingsCategory)=>{
    setActiveCategory(category);
    navigate(`/settings#${category}`,{replace:true});
  };

  return (
    <section className="settings-page">
      <PageHeader eyebrow="PREFERENCES / LOCAL CONFIGURATION" title="Settings"/>
      <div className="settings-container">
        <SettingsSidebar active={activeCategory} onSelect={handleSelect}/>
        <div className="settings-content" role="tabpanel" aria-label="Settings section detail">
          {activeCategory==='appearance'&&<AppearanceTab/>}
          {activeCategory==='colors'&&<ColorsTab/>}
          {activeCategory==='sources'&&<SourcesTab/>}
          {activeCategory==='profile'&&<ProfileTab/>}
        </div>
      </div>
    </section>
  );
}
