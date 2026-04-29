import React, { createContext, useEffect, useContext, useState } from "react";
import api from "../api";

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const checkAuth = async() => {
        try{
            const token = localStorage.getItem("token");

            if(!token){
                setUser(null);
            }else{
                const response = await api.get("/auth/me", {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                })

                setUser(response.data);
            }
        }
        catch(err){
            setUser(null);
            localStorage.removeItem("token");
        }finally{
            setLoading(false);
        }
    } 

    useEffect(() => {
        checkAuth();
    }, []);

    return (
    <AuthContext.Provider value={{ user, loading, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );

}

export const useAuth = () => useContext(AuthContext);
