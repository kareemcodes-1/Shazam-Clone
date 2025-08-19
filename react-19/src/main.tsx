
import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './App.css'
import {BrowserRouter, Routes, Route} from "react-router";
import ToastProvider from './provider/toast-provider.tsx';

createRoot(document.getElementById('root')!).render(
  // <StrictMode>
<BrowserRouter>
  <ToastProvider />
               <Routes>
                   <Route path='/' element={<App />}></Route>
               </Routes>
           </BrowserRouter>
  // </StrictMode>,
)
