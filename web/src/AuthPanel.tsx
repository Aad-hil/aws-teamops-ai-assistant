import React, {useState} from "react";
import {CognitoUserPool, CognitoUser, AuthenticationDetails, CognitoUserAttribute} from "amazon-cognito-identity-js";

type Mode = "signin"|"signup"|"verify"|"forgot"|"reset"|"newPassword"|"pending";
type Props = {pool:CognitoUserPool;onSignedIn:()=>void};
const message = (error:unknown) => error instanceof Error ? error.message : "Authentication failed";
const ALLOWED_GROUP = "teamops-users";

function accountApproved(session:any):boolean {
  const claims = session.getIdToken().decodePayload() as Record<string,unknown>;
  const groups = claims["cognito:groups"];
  if (Array.isArray(groups)) return groups.includes(ALLOWED_GROUP);
  if (typeof groups === "string") return groups.replace(/[\[\]"']/g,"").split(",").map(x=>x.trim()).includes(ALLOWED_GROUP);
  return false;
}

export default function AuthPanel({pool,onSignedIn}:Props){
  const[mode,setMode]=useState<Mode>("signin");
  const[email,setEmail]=useState("");
  const[password,setPassword]=useState("");
  const[confirmPassword,setConfirmPassword]=useState("");
  const[code,setCode]=useState("");
  const[error,setError]=useState("");
  const[notice,setNotice]=useState("");
  const[busy,setBusy]=useState(false);
  const[pendingUser,setPendingUser]=useState<CognitoUser|null>(null);
  const[requiredAttributes,setRequiredAttributes]=useState<Record<string,string>>({});
  const[newPassword,setNewPassword]=useState("");

  const user = () => new CognitoUser({Username:email.trim().toLowerCase(),Pool:pool});
  function changeMode(next:Mode){setMode(next);setError("");setNotice("");setCode("");setPassword("");setConfirmPassword("");}
  function approved(session:any){
    if(accountApproved(session)){onSignedIn();return;}
    pool.getCurrentUser()?.signOut();
    setPassword("");
    setMode("pending");
  }
  async function submit(e:React.FormEvent){
    e.preventDefault();setError("");setNotice("");setBusy(true);
    try{
      if(mode==="signup"){
        if(password!==confirmPassword)throw new Error("Passwords do not match.");
        const address=email.trim().toLowerCase();
        if(!address.includes("@"))throw new Error("Please enter a valid email address.");
        const result=await new Promise<{userConfirmed:boolean}>((resolve,reject)=>{
          pool.signUp(address,password,[new CognitoUserAttribute({Name:"email",Value:address})],[],(err,data)=>{
            if(err || !data)return reject(err||new Error("Sign up failed"));
            resolve({userConfirmed:data.userConfirmed});
          });
        });
        setPassword("");setConfirmPassword("");
        if(result.userConfirmed){setMode("pending");setNotice("Account created. Request access from your TeamOps administrator.");}
        else{setMode("verify");setNotice("We sent a verification code to your email.");}
      } else if(mode==="verify"){
        await new Promise<void>((resolve,reject)=>user().confirmRegistration(code.trim(),true,(err)=>err?reject(err):resolve()));
        setCode("");setMode("signin");setNotice("Email verified. Sign in to check your access status.");
      } else if(mode==="forgot"){
        await new Promise<void>((resolve,reject)=>user().forgotPassword({
          onSuccess:()=>resolve(),onFailure:reject,
          inputVerificationCode:()=>resolve()
        }));
        setMode("reset");setNotice("Enter the reset code sent to your email.");
      } else if(mode==="reset"){
        if(password!==confirmPassword)throw new Error("Passwords do not match.");
        await new Promise<void>((resolve,reject)=>user().confirmPassword(code.trim(),password,{
          onSuccess:()=>resolve(),onFailure:reject
        }));
        setPassword("");setConfirmPassword("");setCode("");setMode("signin");setNotice("Password updated. You can sign in.");
      } else if(mode==="newPassword"){
        if(!pendingUser)throw new Error("Sign in again to complete this step.");
        if(newPassword!==confirmPassword)throw new Error("Passwords do not match.");
        const session=await new Promise<any>((resolve,reject)=>{
          pendingUser.completeNewPasswordChallenge(newPassword,requiredAttributes,{onSuccess:resolve,onFailure:reject});
        });
        setPendingUser(null);setNewPassword("");setConfirmPassword("");
        approved(session);
      } else if(mode==="signin"){
        const cognitoUser=user();
        let needsPasswordChange=false;
        const session=await new Promise<any>((resolve,reject)=>{
          cognitoUser.authenticateUser(new AuthenticationDetails({Username:email.trim().toLowerCase(),Password:password}),{
            onSuccess:resolve,
            onFailure:reject,
            newPasswordRequired:(_attrs:any,required:any)=>{
              needsPasswordChange=true;setPendingUser(cognitoUser);setRequiredAttributes(required||{});resolve(null);
            },
            mfaRequired:()=>reject(new Error("MFA is enabled but not yet supported in this sign-in screen.")),
            totpRequired:()=>reject(new Error("TOTP challenge is not yet supported in this sign-in screen."))
          });
        });
        setPassword("");
        if(needsPasswordChange){setMode("newPassword");return;}
        approved(session);
      }
    }catch(err){setError(message(err));}finally{setBusy(false);}
  }
  async function resend(){
    setError("");setNotice("");setBusy(true);
    try{
      await new Promise<void>((resolve,reject)=>user().resendConfirmationCode(err=>err?reject(err):resolve()));
      setNotice("A new verification code has been sent.");
    }catch(err){setError(message(err));}finally{setBusy(false);}
  }
  function signout(){
    pool.getCurrentUser()?.signOut();setMode("signin");setPassword("");setNotice("");setError("");
  }
  const heading:Record<Mode,string>={
    signin:"Welcome to TeamOps AI",signup:"Create your account",verify:"Verify your email",
    forgot:"Reset your password",reset:"Set a new password",newPassword:"Change temporary password",pending:"Account pending approval"
  };
  return <div className="auth-page"><div className="auth-card">
    <div className="auth-logo">TeamOps AI</div>
    <h1>{heading[mode]}</h1>
    {mode==="pending" ? <>
      <p className="auth-subtitle">Your email is verified, but an administrator must add your account to <code>teamops-users</code> before you can access operational tools.</p>
      {notice&&<p className="auth-notice" role="status">{notice}</p>}
      <button className="auth-primary" type="button" onClick={()=>changeMode("signin")}>Check access by signing in</button>
      <button className="auth-link" type="button" onClick={signout}>Back to sign in</button>
    </> : <>
      <p className="auth-subtitle">{mode==="signup"?"Register using your work email. Access is granted after admin approval.":mode==="verify"?"Enter the code from your verification email.":mode==="forgot"?"We'll email you a password reset code.":mode==="reset"?"Enter the reset code and your new password.":mode==="newPassword"?"Complete the required first-time password update.":"Sign in to your operations workspace."}</p>
      <form className="auth-form" onSubmit={submit}>
        {mode!=="newPassword" && <label>Email<input type="email" required autoComplete="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="you@example.com" disabled={busy||mode==="verify"} /></label>}
        {(mode==="verify"||mode==="reset")&&<label>Verification code<input required inputMode="numeric" autoComplete="one-time-code" value={code} onChange={e=>setCode(e.target.value)} placeholder="Enter code" /></label>}
        {(mode==="signin"||mode==="signup"||mode==="reset")&&<label>Password<input type="password" required minLength={mode==="signin"?undefined:8} autoComplete={mode==="signin"?"current-password":"new-password"} value={password} onChange={e=>setPassword(e.target.value)} placeholder="Password"/></label>}
        {mode==="newPassword"&&<label>New password<input type="password" required minLength={8} autoComplete="new-password" value={newPassword} onChange={e=>setNewPassword(e.target.value)} placeholder="New password"/></label>}
        {(mode==="signup"||mode==="reset"||mode==="newPassword")&&<label>Confirm password<input type="password" required autoComplete="new-password" value={confirmPassword} onChange={e=>setConfirmPassword(e.target.value)} placeholder="Confirm password"/></label>}
        {error&&<p role="alert" className="auth-error">{error}</p>}
        {notice&&<p role="status" className="auth-notice">{notice}</p>}
        <button className="auth-primary" disabled={busy} type="submit">{busy?"Please wait…":({signin:"Sign in",signup:"Create account",verify:"Verify email",forgot:"Send reset code",reset:"Update password",newPassword:"Set password",pending:""} as Record<Mode,string>)[mode]}</button>
      </form>
      <div className="auth-actions">
        {mode==="signin"&&<><button className="auth-link" onClick={()=>changeMode("signup")}>Create account</button><button className="auth-link" onClick={()=>changeMode("forgot")}>Forgot password?</button><button className="auth-link" onClick={()=>changeMode("verify")}>Verify existing account</button></>}
        {mode==="verify"&&<button className="auth-link" onClick={()=>void resend()} disabled={busy}>Resend verification code</button>}
        {mode!=="signin"&&<button className="auth-link" onClick={()=>changeMode("signin")}>Back to sign in</button>}
      </div>
    </>}
  </div></div>;
}
