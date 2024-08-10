import React from 'react';
import { MainChart } from './components/MainChart';
import './App.css';
import Layout from "./Layout";

function App() {
  return (
      <Layout>
        <div className="App">
          <MainChart />
        </div>
      </Layout>
  );
}

export default App;
