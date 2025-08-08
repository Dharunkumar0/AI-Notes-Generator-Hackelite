@router.post("/analyze-emotion", response_model=EmotionAnalysisResponse)
async def analyze_voice_emotion_endpoint(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """Analyze voice recording to detect emotional state and provide relevant suggestions."""
    try:
        start_time = time.time()
        
        # First, transcribe the audio
        transcribe_result = await transcribe_audio_file(file, current_user)
        
        if not transcribe_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to transcribe audio"
            )
        
        # Get audio data for emotion analysis
        await file.seek(0)
        audio_data = await file.read()
        
        # Analyze emotion using both audio data and transcription
        emotion_result = await analyze_voice_emotion(
            audio_data=audio_data,
            transcription=transcribe_result["transcription"]
        )
        
        if not emotion_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Emotion analysis failed: {emotion_result['error']}"
            )
        
        processing_time = time.time() - start_time
        
        # Save to history
        history_data = HistoryCreate(
            user_id=str(current_user.id),
            feature_type="voice_emotion",
            input_data={
                "filename": file.filename,
                "transcription_length": len(transcribe_result["transcription"].split())
            },
            output_data={
                "primary_emotion": emotion_result["data"]["primary_emotion"],
                "emotion_scores": emotion_result["data"]["emotion_scores"]
            },
            processing_time=processing_time
        )
        
        history_collection = get_collection("history")
        await history_collection.insert_one(history_data.dict(by_alias=True))
        
        # Add processing time to result
        emotion_result["data"]["processing_time"] = processing_time
        
        return emotion_result["data"]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing voice emotion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze voice emotion: {str(e)}"
        )
